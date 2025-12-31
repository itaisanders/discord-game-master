import os
import time
import pathlib
import argparse
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash-lite")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash-lite")
OUTPUT_DIR = "knowledge"

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def upload_to_gemini(file_path: pathlib.Path):
    """Uploads a file to Gemini and waits for it to be active."""
    print(f"☁️  Uploading {file_path.name} to Gemini...")
    try:
        f_obj = client.files.upload(file=str(file_path))
    except Exception as e:
        print(f"❌ Upload failed for {file_path}: {e}")
        return None

    # Wait for processing
    print("⏳ Waiting for Gemini to process file...")
    while f_obj.state.name == "PROCESSING":
        time.sleep(2)
        f_obj = client.files.get(name=f_obj.name)
    
    if f_obj.state.name != "ACTIVE":
        print(f"❌ File {f_obj.name} failed processing: {f_obj.state.name}")
        return None
            
    print("✅ File active and ready.")
    return f_obj

def load_persona():
    current_dir = pathlib.Path(__file__).parent
    persona_path = current_dir / "art_analyzer_persona.md"
    
    if persona_path.exists():
        return persona_path.read_text(encoding="utf-8").strip()
    return "Analyze the visual style of the provided PDF and create a styleguide."

def run_analysis(pdf_path_str):
    pdf_path = pathlib.Path(pdf_path_str)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return

    # 1. Upload
    remote_file = upload_to_gemini(pdf_path)
    if not remote_file:
        return

    # 2. Prepare Prompt
    persona = load_persona()
    prompt = f"Analyze the entire visual style of this book: {pdf_path.name}. Provide a comprehensive Styleguide as instructed."

    print(f"🧠 Analyzing Artwork with {AI_MODEL}...")
    
    try:
        response = client.models.generate_content(
            model=AI_MODEL,
            contents=[remote_file, prompt],
            config=types.GenerateContentConfig(
                system_instruction=persona,
                temperature=0.2
            )
        )
        
        if response.text:
            # 3. Save Output
            pathlib.Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
            output_file = pathlib.Path(OUTPUT_DIR) / f"{pdf_path.stem}.style"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            print(f"✨ Success! Styleguide saved to: {output_file}")
            print("-" * 40)
            print(response.text[:500] + "...") # Preview
            print("-" * 40)
        else:
            print("❌ Error: Received empty response from GEMINI.")

    except Exception as e:
        print(f"❌ Fatal Error during analysis: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RPG Art Architect: Visual Style Analyzer")
    parser.add_argument("pdf_path", nargs="?", help="Path to the PDF file. If omitted, looks in the /pdf folder.")
    args = parser.parse_args()

    target_pdf = args.pdf_path

    if not target_pdf:
        # Auto-detect in /pdf folder
        pdf_dir = pathlib.Path("./pdf")
        if pdf_dir.exists():
            pdfs = list(pdf_dir.glob("*.pdf"))
            if pdfs:
                target_pdf = str(pdfs[0])
                print(f"📂 Auto-detected PDF: {target_pdf}")
            else:
                print("❌ No PDFs found in ./pdf/ directory.")
                exit(1)
        else:
            print("❌ No PDF provided and ./pdf/ directory does not exist.")
            exit(1)

    run_analysis(target_pdf)

def _syntax_check():
    """A simple function to confirm the file is syntactically correct."""
    return True