import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

# New imports to stop warnings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from django.conf import settings

# 1. FORCE LOAD ENV
# This ensures that even if you start the server from different folders, it finds your keys
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

# --- DEBUG CHECK (Visible in Terminal) ---
print(f"--- ENGINE STARTING ---")
print(f"Looking for .env at: {os.path.join(BASE_DIR, '.env')}")
print(f"Groq Key Loaded: {bool(os.getenv('GROQ_API_KEY'))}")
print(f"Gemini Key Loaded: {bool(os.getenv('GOOGLE_API_KEY'))}")

# 2. PATHS & EMBEDDINGS
PERSIST_DIRECTORY = os.path.join(settings.BASE_DIR, "research", "chroma_db_e5")
EMBEDDING_MODEL_NAME = "intfloat/e5-large-v2"

embedding_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

vectorstore = Chroma(
    collection_name="study_abroad_e5_large",
    embedding_function=embedding_model,
    persist_directory=PERSIST_DIRECTORY
)

print(
    f"CHROMA DB STATUS: Successfully loaded {vectorstore._collection.count()} documents.")

# 3. UPDATED 2026 MODEL PRIORITY
MODEL_PRIORITY = [
    {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    {"provider": "google", "model": "gemini-3.1-pro-preview"},  # Latest 2026 Model
    {"provider": "cerebras", "model": "llama-3.3-70b"},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-latest"}
]


class MultiPlatformManager:
    def get_client(self, provider):
        key = os.getenv(f"{provider.upper()}_API_KEY")
        if not key:
            return None

        try:
            if provider == "google":
                return genai.Client(api_key=key)
            if provider == "groq":
                # Groq uses the OpenAI-compatible client
                return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            if provider == "openai":
                return OpenAI(api_key=key)
            if provider == "cerebras":
                return OpenAI(api_key=key, base_url="https://api.cerebras.ai/v1")
            if provider == "anthropic":
                return anthropic.Anthropic(api_key=key)
        except Exception as e:
            print(f"Client Setup Error for {provider}: {e}")
            return None
        return None


manager = MultiPlatformManager()

# 4. MAIN CHAT FUNCTION


def ask_study_abroad_bot(user_query, k=4):
    search_query = f"2026 UK international student {user_query}"

    # 1. Retrieval logic with DB Visibility
    try:
        search_results = vectorstore.similarity_search(search_query, k=10)

        if not search_results:
            print("DB WARNING: No local documents found for this query.")
            # context_text = "No local data found. Use general 2026 UK education knowledge."

            context_text = "\n--- NEW DATA SOURCE ---\n".join([
                f"FROM FILE: {d.metadata.get('source')}\nCONTENT: {d.page_content}"
                for d in search_results
            ])
        else:
            print(
                f"DB SUCCESS: Found {len(search_results)} matching documents.")
            context_text = "\n\n".join([
                f"SOURCE: {d.metadata.get('source', 'Unknown')}\n{d.page_content}"
                for d in search_results
            ])
    except Exception as e:
        print(f"Database Error: {e}")
        context_text = "No local data found. Use general 2026 UK education knowledge."

    # 2. Strict Formatting Logic (Ensures tables/bullets render correctly)
    sys_prompt = """You are the 'Senior  Education Lead' for 2026. 
    CRITICAL FORMATTING RULES:
    CORE MISSION: Provide the MOST DETAILED answer possible. 
    1. TABLES: You must use standard Markdown tables. 
    - You MUST include the separator line: | Header | Header |
                                        |---|---|
    - ALWAYS leave one empty line before and after a table.
   2. LISTS: Use '*' for bullet points and ensure there is a space after the '*'.
   3. DO NOT use plain text for comparisons; ALWAYS use a table.
   4. If data is not in the provided context, clearly state it is an '2026 estimate
   5. If asked about fees, do not summarize. List every university and faculty found in the context.
   6. If the context is large, create multiple tables for different subject areas (e.g., STEM, Arts, Business).
   7. Your responses should be long, professional, and data-heavy.
   8. Always leave an empty line before and after tables to ensure proper rendering."""

    user_prompt = f"CONTEXT FROM DATABASE:\n{context_text}\n\nUSER QUESTION: {user_query}"

    # Routing logic
    for target in MODEL_PRIORITY:
        provider = target["provider"]
        model_id = target["model"]

        try:
            client = manager.get_client(provider)
            if not client:
                continue

            if provider == "google":
                resp = client.models.generate_content(
                    model=model_id,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt)
                )
                return resp.text

            elif provider in ["openai", "groq", "cerebras"]:
                resp = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2
                )
                return resp.choices[0].message.content

            elif provider == "anthropic":
                resp = client.messages.create(
                    model=model_id,
                    max_tokens=2048,
                    system=sys_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return resp.content[0].text

        except Exception as e:
            # Only print first 100 chars of error
            print(f"{provider} failed: {str(e)[:100]}")
            continue

    return "Sorry, I am having trouble connecting to my AI brains. Please check your API keys."
