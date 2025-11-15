from fastapi import FastAPI, Query
from collections import Counter
from app.data_client import fetch_member_messages, fetch_raw_messages
from app.qa_engine import answer_question_baseline

app = FastAPI(
    title="Aurora QA Service",
    description="Simple question-answering service over Aurora member messages.",
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ask")
def ask(question: str = Query(..., description="Natural-language question about a member")):
    """
    Main endpoint: given a question, returns an answer inferred from /messages.
    """
    messages = fetch_member_messages()
    answer = answer_question_baseline(question, messages)
    return {"answer": answer}

@app.get("/debug/messages_sample")
def messages_sample():
    """
    Debug endpoint: returns a small sample of the raw /messages data
    so we can inspect the actual JSON structure.
    """
    raw = fetch_raw_messages()
    # Return only first few items to avoid huge responses
    if isinstance(raw, list):
        return raw[:5]
    return raw

@app.get("/debug/member_names")
def member_names():
    """
    Debug endpoint: show all distinct member names and how many messages each has.
    """
    messages = fetch_member_messages()
    counts = Counter()

    for m in messages:
        name = (m.member_name or "").strip()
        counts[name] += 1

    # Convert Counter to a normal dict so FastAPI can serialize it
    return dict(counts)