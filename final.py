from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi import FastAPI,Request
import base64
app = FastAPI()
import re

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
    "Authorization": f"B",
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
    context = "\n".join(load_markdown_from_repo("RachanaMuthukumar", "AiBot")) or "No markdown content available."

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
    print("Watson NLU response status:", response.status_code)
    print("Watson NLU raw response:", response.text)

    if response.status_code == 200:
        result = response.json()

        # Extract keyword + entity terms
        terms = [item["text"].lower() for item in result.get("keywords", []) + result.get("entities", [])]
        query_terms = query.split()

        # Emergency and medical keywords
        emergency_terms = ["police", "emergency", "helpline", "crime", "fire", "ambulance", "100", "101", "102", "112"]
        medical_terms = ["cardiology", "cardiologgy", "heart", "cardiac", "chest pain"]

        # Intent detection
        def detect_intent(query):
            query = query.lower()
            if any(word in query for word in emergency_terms):
                return "emergency"
            elif any(word in query for word in medical_terms):
                return "cardiology"
            else:
                return "general"

        intent = detect_intent(query)

        # Text normalization helpers
        def normalize(text):
            return re.sub(r"[^\w\s]", "", text.lower())

        def word_match(line, words):
            line_words = set(normalize(line).split())
            return sum(1 for word in words if word in line_words)

        # Normalize query and NLU terms
        normalized_query_terms = [normalize(q) for q in query_terms]
        normalized_nlu_terms = [normalize(t) for t in terms]

        # Intent-based matching
        if intent == "emergency":
    # Detect sub-intent: police, fire, ambulance
            emergency_type = None
            for keyword in ["police", "fire", "ambulance","childline"]:
                if keyword in query:
                    emergency_type = keyword
                    break

            matched_lines = [
                line for line in context.split('\n')
                if emergency_type and emergency_type in line.lower()
                and len(line.strip()) > 30
                and not line.strip().startswith("#")
            ]

            # Fallback to general emergency info
            if not matched_lines:
                matched_lines = [
                    line for line in context.split('\n')
                    if "112" in line or "emergency" in line.lower()
                    and len(line.strip()) > 30
                    and not line.strip().startswith("#")
                ]

        elif intent == "cardiology":
            matched_lines = [
                line for line in context.split('\n')
                if word_match(line, medical_terms + normalized_query_terms) >= 1
                and len(line.strip()) > 30
                and not line.strip().startswith("#")
            ]
        else:
            # General fallback using NLU terms
            matched_lines = [
                line for line in context.split('\n')
                if word_match(line, normalized_nlu_terms) >= 1
                and len(line.strip()) > 30
                and not line.strip().startswith("#")
            ]

        # Final filtering and response
        filtered_lines = [
            line.strip() for line in matched_lines
            if len(line.strip()) > 30 and not line.strip().startswith("#")
        ]

        # Fallbacks based on intent
        if filtered_lines:
            answer = filtered_lines[0]
        elif intent == "cardiology":
            answer = "Cardiology is the medical specialty focused on heart health and diseases."
        elif intent == "emergency":
            answer = "**112** is India's all-in-one emergency number (like 911 in the US)."
        else:
            answer = "I couldn't find a direct answer. Could you rephrase your question?"

        answer = re.sub(r"\*\*(.*?)\*\*", r"\1", answer)

        return {"response": answer}
    else:
        return {
            "error": f"Watson NLU returned status code {response.status_code}.",
            "details": response.json()
        }
