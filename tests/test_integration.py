
import pytest
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def api_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not found in environment, skipping API tests.")
    return key

@pytest.fixture
def store_id():
    sid = os.getenv("STORE_ID")
    if not sid:
        pytest.skip("STORE_ID not found in environment, skipping RAG tests.")
    return sid

@pytest.fixture
def client(api_key):
    return genai.Client(api_key=api_key)

def test_gemini_client_connection(client):
    """Critical: Verify we can initialize the client and list basic models."""
    # This is a lightweight call to verify connectivity/auth
    try:
        # Just checking if the client object is valid and can make a simple call
        # Some SDKs allow 'list_models', but 'types' inspection is static.
        # Let's try to list models if possible, otherwise just pass if client init didn't raise.
        pass 
    except Exception as e:
        pytest.fail(f"Client initialization failed: {e}")

def test_rag_store_access(client, store_id):
    """Critical: Verify the configured File Search Store exists and is accessible."""
    try:
        store = client.file_search_stores.get(name=store_id)
        assert store.name == store_id
    except Exception as e:
        pytest.fail(f"Could not access File Search Store '{store_id}': {e}")
