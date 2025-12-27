import os
import pathlib
import argparse
import pymupdf
import pymupdf4llm
from dotenv import load_dotenv

# 1. Configuration
load_dotenv()
OUTPUT_DIR = "knowledge"

def ask_user_reuse(file_path: pathlib.Path) -> bool:
    """Prompts the user to decide whether to reuse an existing file."""
    if not file_path.exists():
        return False
    
    while True:
        choice = input(f"📝 Found existing file: {file_path.name}\n   Would you like to overwrite it? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            print(f"   -> Overwriting {file_path.name}...")
            return False
        if choice in ['n', 'no']:
            print(f"   -> Keeping existing {file_path.name}")
            return True
        print("   Please enter 'y' for yes or 'n' for no.")

def process_book(pdf_target):
    """Generates a high-fidelity markdown file from the PDF using pymupdf4llm."""
    path_obj = pathlib.Path(pdf_target)
    base_name = path_obj.stem
    
    # Ensure OUTPUT_DIR exists
    pathlib.Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    final_output_path = pathlib.Path(OUTPUT_DIR) / f"{base_name}_transcribed.md"

    if ask_user_reuse(final_output_path):
        print(f"✅ Ingestion skipped. Using existing: {final_output_path}")
        return

    print(f"⚙️  Extracting markdown from {pdf_target}...")
    print( "   (This uses pymupdf4llm for high-fidelity layout preservation)")
    
    try:
        # Pymupdf4llm Extraction
        md_content = pymupdf4llm.to_markdown(str(path_obj))
        
        with open(final_output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"✅ Success! Transcribed file saved to: {final_output_path}")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local High-Fidelity RPG Ingestor")
    parser.add_argument("pdf_path", help="Path to the PDF file to ingest")
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"❌ File not found: {args.pdf_path}")
        exit(1)
        
    process_book(args.pdf_path)


def _syntax_check():
    """A simple function to confirm the file is syntactically correct."""
    return True