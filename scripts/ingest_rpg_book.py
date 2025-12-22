
import os
import time
import pathlib
import argparse
import threading
import itertools
import sys
import pymupdf
import pymupdf.layout
import pymupdf4llm
from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tqdm import tqdm

# 1. Configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash-lite")
PERSONA_PATH = "personas/rpg_scribe_instructions.md"
OUTPUT_DIR = "knowledge"

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

class ProgressSpinner:
    """A simple thread-based spinner for long-running operations."""
    def __init__(self, message="Working"):
        self.message = message
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
        self.stop_running = threading.Event()
        self.thread = threading.Thread(target=self._animate)

    def _animate(self):
        while not self.stop_running.is_set():
            sys.stdout.write(f"\r  {next(self.spinner)} {self.message}...")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r") # Clear line

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_running.set()
        self.thread.join()

def ask_user_reuse(file_path: pathlib.Path) -> bool:
    """Prompts the user to decide whether to reuse an existing file."""
    if not file_path.exists():
        return False
    
    while True:
        choice = input(f"📝 Found existing file: {file_path.name}\n   Would you like to reuse it? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            print(f"   -> Reusing {file_path.name}")
            return True
        if choice in ['n', 'no', 'r', 'recreate']:
            print(f"   -> Recreating {file_path.name}...")
            return False
        print("   Please enter 'y' for yes or 'n' for no.")

def preprocess_pdf(pdf_path: str):
    """Generates markdown and raw text dumps from the PDF."""
    print(f"⚙️  Pre-processing {pdf_path}...")
    
    path_obj = pathlib.Path(pdf_path)
    base_name = path_obj.stem
    
    # Ensure OUTPUT_DIR exists
    pathlib.Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    md_path = pathlib.Path(OUTPUT_DIR) / f"{base_name}_dump.md"
    txt_path = pathlib.Path(OUTPUT_DIR) / f"{base_name}_raw.txt"

    # 1. Pymupdf4llm Markdown Dump (Layout Aware)
    if not ask_user_reuse(md_path):
        print("   - Generating Markdown dump (pymupdf4llm + layout AI)...")
        with ProgressSpinner("Analyzing layout and extracting markdown"):
            doc = pymupdf.open(pdf_path)
            md_content = pymupdf4llm.to_markdown(doc)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            doc.close()

    # 2. PyPDF Raw Text Dump (Layout mode)
    if not ask_user_reuse(txt_path):
        print("   - Generating Raw Text dump (pypdf layout)...")
        with ProgressSpinner("Extracting text layers"):
            reader = PdfReader(pdf_path)
            with open(txt_path, "w", encoding="utf-8") as f:
                for page in reader.pages:
                    f.write(page.extract_text(extraction_mode="layout") + "\n\n")
    
    # We need the page count regardless of reuse
    reader = PdfReader(pdf_path)
    return path_obj, md_path, txt_path, len(reader.pages)

def upload_to_gemini(files):
    """Uploads files to Gemini and waits for them to be active."""
    uploaded_files = []
    print(f"☁️  Uploading {len(files)} files to Gemini...")
    
    for file_path in files:
        with ProgressSpinner(f"Uploading {file_path.name}"):
            try:
                 op = client.files.upload(file=str(file_path))
                 uploaded_files.append(op)
            except Exception as e:
                print(f"❌ Upload failed for {file_path}: {e}")
                return None

    # Wait for processing
    print("⏳ Waiting for Gemini to process files...")
    for f_obj in uploaded_files:
        with ProgressSpinner(f"Processing {f_obj.name}"):
            while f_obj.state.name == "PROCESSING":
                time.sleep(2)
                f_obj = client.files.get(name=f_obj.name)
        
        if f_obj.state.name != "ACTIVE":
            print(f"❌ File {f_obj.name} failed processing: {f_obj.state.name}")
            return None
            
    print("✅ All files active and ready.")
    return uploaded_files

def load_scribe_persona():
    if os.path.exists(PERSONA_PATH):
        with open(PERSONA_PATH, "r") as f:
            return f.read().strip()
    return "Transcribe the PDF into Markdown."

def process_book(pdf_target, keep_temp=False):
    # 2. Pre-process
    pdf_path, md_path, txt_path, total_pages = preprocess_pdf(pdf_target)
    
    # 3. Upload
    remote_files = upload_to_gemini([pdf_path, md_path, txt_path])
    if not remote_files:
        return

    sys_instruction = load_scribe_persona()
    
    # Check for existing final transcription
    final_output_path = pathlib.Path(OUTPUT_DIR) / f"{pdf_path.stem}_transcribed.md"
    if ask_user_reuse(final_output_path):
        print(f"✅ Ingestion skipped. Using existing: {final_output_path}")
        return

    # 4. Mirror Loop
    output_markdown = []
    chunk_size = 5
    
    print(f"🔄 Starting Transcription Loop ({total_pages} pages total)...")
    
    # Using tqdm for the transcription loop progress bar
    total_steps = (total_pages + chunk_size - 1) // chunk_size
    success = True
    error_msg = ""
    
    with tqdm(total=total_steps, desc="📚 Transcribing", unit="chunk") as pbar:
        for start_page in range(1, total_pages + 1, chunk_size):
            end_page = min(start_page + chunk_size - 1, total_pages)
            
            prompt = f"""
            Transcribe pages {start_page} to {end_page} VERBATIM using the provided references.
            Refer to the RAW TEXT dump and MARKDOWN dump for vocabulary accuracy.
            Refer to the PDF visuals for layout structure.
            
            Output ONLY the final clean markdown content in a code block.
            Do not include introductory text.
            """

            try:
                response = client.models.generate_content(
                    model=AI_MODEL,
                    contents=[
                        *remote_files,
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instruction,
                        temperature=0.1
                    )
                )
                
                if response.text:
                    content = response.text.replace("```markdown", "").replace("```", "").strip()
                    output_markdown.append(content)
                else:
                    # Treat empty response as a failure to ensure data integrity
                    success = False
                    error_msg = f"Empty response for pages {start_page}-{end_page}"
                    break
                    
            except Exception as e:
                success = False
                error_msg = str(e)
                break
            
            pbar.update(1)

    if not success:
        progress = (pbar.n / total_steps) * 100
        print(f"\n❌ FATAL ERROR: Transcription failed at {progress:.1f}% completion.")
        print(f"🛑 Reason: {error_msg}")
        # Cleanup and exit if not keeping temp
        if not keep_temp:
            md_path.unlink(missing_ok=True)
            txt_path.unlink(missing_ok=True)
        return

    # 5. Aggregate
    print("✨ Finalizing document...")
    final_content = "\n\n".join(output_markdown)
    
    pathlib.Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    final_output_path = pathlib.Path(OUTPUT_DIR) / f"{pdf_path.stem}_transcribed.md"
    
    with open(final_output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print(f"✅ Success! Transcribed file saved to: {final_output_path}")
    
    # Cleanup
    if not keep_temp:
        md_path.unlink(missing_ok=True)
        txt_path.unlink(missing_ok=True)
        print("🧹 Temporary workspace cleaned.")
    else:
        print(f"📂 Temporary files preserved in {OUTPUT_DIR}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="High-Fidelity RPG Scribe")
    parser.add_argument("pdf_path", help="Path to the PDF file to ingest")
    parser.add_argument("--keep-temp", action="store_true", help="Do not delete temporary reference files after processing")
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"❌ File not found: {args.pdf_path}")
        exit(1)
        
    process_book(args.pdf_path, keep_temp=args.keep_temp)
