import os
import requests
from typing import List
from app.models import MemberMessage

# Default URL – from assignment
AURORA_MESSAGES_URL = os.getenv(
    "AURORA_MESSAGES_URL",
    "https://november7-730026606190.europe-west1.run.app/messages",
)

def fetch_raw_messages():
    """
    Call Aurora's /messages endpoint and return the raw JSON.
    """
    resp = requests.get(AURORA_MESSAGES_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_member_messages() -> List[MemberMessage]:
    """
    Fetch messages from Aurora's /messages API and convert them
    into our internal MemberMessage objects.
    """
    raw = fetch_raw_messages()

    # According to the API, raw looks like:
    # {
    #   "total": 3349,
    #   "items": [ { ...message... }, ... ]
    # }
    items = raw.get("items", [])

    messages: List[MemberMessage] = []
    for item in items:
        msg = MemberMessage(
            member_id=item.get("user_id"),
            member_name=item.get("user_name"),
            text=item.get("message", ""),
            created_at=item.get("timestamp"),
        )
        messages.append(msg)

    return messages