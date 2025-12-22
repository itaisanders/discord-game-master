import os
import time
import pathlib
from dotenv import load_dotenv, set_key
from google import genai

def index_knowledge():
    """Reads PDF files from the pdf folder and indexes them using Google GenAI."""
    
    # 1. Setup: Load GEMINI_API_KEY from .env
    env_path = ".env"
    load_dotenv(env_path)
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file.")
        return

    try:
        # Initialize the google-genai client
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ Error: Failed to initialize Google GenAI client - {e}")
        return

    # 2. File Handling: Scan './pdf' for .pdf files
    pdf_dir = pathlib.Path("./pdf")
    if not pdf_dir.exists():
        print(f"❌ Error: Folder '{pdf_dir.absolute()}' does not exist.")
        return

    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"⚠️ Warning: No .pdf files found in '{pdf_dir.absolute()}'.")
        return

    print(f"📂 Found {len(pdf_files)} PDF file(s) for indexing.")

    # 3. RAG Indexing
    try:
        # Create a new file_search_store
        print("🚀 Creating File Search Store: 'Discord_Bot_Knowledge'...")
        store = client.file_search_stores.create(
            config={"display_name": "Discord_Bot_Knowledge"}
        )
        store_id = store.name
        print(f"🆔 New Store ID: {store_id}")

        indexed_files = []
        operations = []

        # Upload all detected PDFs
        for pdf_path in pdf_files:
            print(f"📤 Uploading: {pdf_path.name}...")
            # upload_to_file_search_store returns an operation
            operation = client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=store_id,
                file=str(pdf_path)
            )
            operations.append((pdf_path.name, operation))

        # Wait for operations to complete
        print("⏳ Processing and indexing files... (this may take a few moments)")
        for file_name, op in operations:
            # Poll for completion
            while not op.done:
                time.sleep(2)
                op = client.operations.get(operation=op)
            
            if op.error:
                print(f"❌ Error indexing {file_name}: {op.error}")
            else:
                indexed_files.append(file_name)
                print(f"✅ {file_name} indexed successfully.")

        # 4. Automation: Append or update STORE_ID in .env
        set_key(env_path, "STORE_ID", store_id)
        print("💾 Updated .env with STORE_ID.")

        # 5. Verification: Print results
        print("\n" + "═" * 40)
        print("📁 INDEXING VERIFICATION")
        print("═" * 40)
        print(f"Total Files Indexed: {len(indexed_files)}")
        for f in indexed_files:
            print(f"  • {f}")
        print(f"Final Store ID: {store_id}")
        print("═" * 40)
        print("✨ Indexing complete and environment updated.")

    except Exception as e:
        print(f"❌ An error occurred during the indexing process: {e}")

if __name__ == "__main__":
    index_knowledge()
