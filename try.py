from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi import FastAPI,Request
import base64
import re
from difflib import SequenceMatcher
from functools import lru_cache
app = FastAPI()

# CORS setup
origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # <-- allows OPTIONS implicitly
    allow_headers=["Content-Type", "Authorization"],
)

# Watson NLU configuration
api_key = ""  # 🔑 Replace with your actual API key
auth_string = f"apikey:{api_key}"
auth_encoded = base64.b64encode(auth_string.encode()).decode()

nlu_headers = {
    "Authorization": f"Basic {auth_encoded}",
    "Content-Type": "application/json"
}

watson_nlu_url = "https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/36d32e4a-29bf-4810-8839-6378c1bbd1b5/v1/analyze?version=2022-04-07"
# Load markdown from GitHub
def load_markdown_from_repo(user, repo, branch="main"):
    api_url = f"https://api.github.com/repos/"
    headers = {
    "Authorization": f"", 
    "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(api_url, headers=headers)
    markdown_contents = []

    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file['name'].endswith('.md'):
                raw_url = file['download_url']
                md_response = requests.get(raw_url)
                if md_response.status_code == 200:
                    markdown_contents.append(md_response.text)
    else:
        print(f" Failed to fetch repo contents: {response.status_code} - {response.text}")
    return markdown_contents

@app.post("/ask")
async def ask_question(request: Request):
    body = await request.json()
    query = body.get("question", "").strip().lower()

    if not query:
        return {"error": "Question field is empty."}

    # Handle greetings separately
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]
    if query in greetings:
        return {"response": "Hi there! How can I assist you today?"}

    # Load markdown context from GitHub
    context = "\n".join(load_markdown_from_repo("", "")) or "No markdown content available."

    # Prepare combined text for NLU
    combined_text = f"""
Use the following documentation to extract insights based on the user's query.

Context:
{context[:6000]}

User Question:
{query}
""".strip()

    # NLU payload
    nlu_payload = {
        "text": combined_text,
        "features": {
            "keywords": {"limit": 10},
            "entities": {"limit": 10}
        },
        "language": "en",
        "version": "2022-04-07"
    }

    response = requests.post(watson_nlu_url, headers=nlu_headers, json=nlu_payload)
    print("🔍 Watson NLU response status:", response.status_code)
    print("📝 Watson NLU raw response:", response.text)

    if response.status_code == 200:
        result = response.json()

        # Extract keyword + entity terms
        terms = [item["text"].lower() for item in result.get("keywords", []) + result.get("entities", [])]
        query_terms = query.split()

        emergency_terms = ["police", "emergency", "helpline", "crime", "fire", "ambulance", "100", "112"]

        # Match lines with high relevance
        # Step 1: Try exact query term match
        # Step 1: Try exact query term match
        matched_lines = [
            line for line in context.split('\n')
            if any(q in line.lower() for q in query_terms)
            and len(line.strip()) > 30
            and not line.strip().startswith("#")
        ]

        # Step 2: Fallback to NLU term match
        if not matched_lines:
            matched_lines = [
                line for line in context.split('\n')
                if any(term in line.lower() for term in terms)
                and len(line.strip()) > 30
                and not line.strip().startswith("#")
            ]


        # Filter out markdown headings and short fragments
        filtered_lines = [
            line.strip() for line in matched_lines
            if len(line.strip()) > 30 and not line.strip().startswith("#")
        ]

        # Return the first meaningful line or fallback
        answer = filtered_lines[0] if filtered_lines else "Cardiology is the medical specialty focused on heart health and diseases."

        # Remove Markdown bold (**text**) formatting
        answer = re.sub(r"\*\*(.*?)\*\*", r"\1", answer)

        return {"response": answer}
    else:
        return {
            "error": f"Watson NLU returned status code {response.status_code}.",
            "details": response.json()
        }
