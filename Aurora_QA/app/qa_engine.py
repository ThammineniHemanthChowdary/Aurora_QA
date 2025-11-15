from typing import List, Optional
import re

from app.models import MemberMessage


# ---------- Helper: find member in question ----------

def find_member_name_in_question(question: str, messages: List[MemberMessage]) -> Optional[str]:
    """
    Try to detect which member the question is about.

    Strict strategy:
    1) Exact full-name match (e.g., "Sophia Al-Farsi").
    2) Unique first-name match (e.g., "Layla" if only one Layla exists).
    3) Non-unique first-name match: pick the member with that first name
       who appears most often in the messages.
    """
    if not messages:
        return None

    q_lower = question.lower()
    # All distinct member names
    unique_names = {m.member_name for m in messages if m.member_name}

    # --- Precompute per-member message counts ---
    msg_counts: dict[str, int] = {}
    for m in messages:
        if m.member_name:
            msg_counts[m.member_name] = msg_counts.get(m.member_name, 0) + 1

    # Normalize question into tokens (words)
    tokens = re.findall(r"[a-zA-Z]+", q_lower)  # "Amira's" -> ["amira", "s"]

    # ---------- 1) Full-name substring match ----------
    # Highest precision: if the full name literally appears in the question
    for name in sorted(unique_names, key=len, reverse=True):
        if not name:
            continue
        if name.lower() in q_lower:
            return name

    # ---------- 2) First-name map ----------
    by_first: dict[str, List[str]] = {}
    for name in unique_names:
        parts = name.split()
        if not parts:
            continue
        first = parts[0].lower()
        by_first.setdefault(first, []).append(name)

    # 2a) Unique first-name: safe to pick directly (this is how Layla works)
    for token in tokens:
        if token in by_first and len(by_first[token]) == 1:
            return by_first[token][0]

    # 2b) Non-unique first-name:
    #     If there are multiple people with that first name,
    #     choose the one with the MOST messages.
    best_name = None
    best_score = 0
    for token in tokens:
        if token in by_first and len(by_first[token]) > 1:
            candidates = by_first[token]
            for name in candidates:
                score = msg_counts.get(name, 0)
                if score > best_score:
                    best_score = score
                    best_name = name

    if best_name:
        return best_name

    # No strict match
    return None


def extract_requested_first_name(question: str) -> Optional[str]:
    """
    Try to pull out the first-name token the user is asking about.
    Handles patterns like "Amira's favorite ..." or
    "What are Amira's favorite restaurants?"
    """
    # Pattern like "Amira's"
    m = re.search(r"\b([A-Za-z]+)'s\b", question)
    if m:
        return m.group(1)

    # Fallback: grab a capitalized word that is not at the very start
    # (to avoid matching "What", "When", etc.)
    tokens = question.split()
    for i, tok in enumerate(tokens):
        if i == 0:
            continue  # skip first word "What/When/How"
        if tok and tok[0].isupper():
            # Strip trailing punctuation like "Amira?"
            cleaned = re.sub(r"[^\w]", "", tok)
            if cleaned:
                return cleaned

    return None


def suggest_similar_member_by_first_name(
    requested_first_name: str,
    messages: List[MemberMessage],
    min_similarity: float = 0.80,
) -> Optional[str]:
    """
    Given a first name from the question (e.g., 'Amira'),
    suggest the closest member's full name by first name
    (e.g., 'Amina Van Den Berg') if similarity is high enough.
    """
    from difflib import SequenceMatcher

    requested = requested_first_name.lower()
    unique_names = {m.member_name for m in messages if m.member_name}

    best_full_name = None
    best_ratio = 0.0

    for full_name in unique_names:
        parts = full_name.split()
        if not parts:
            continue
        first = parts[0].lower()
        ratio = SequenceMatcher(None, requested, first).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_full_name = full_name

    if best_full_name and best_ratio >= min_similarity:
        return best_full_name

    return None



def filter_messages_for_member(messages: List[MemberMessage], member_name: str) -> List[MemberMessage]:
    """Return all messages for a given member name."""
    return [m for m in messages if m.member_name == member_name]


# ---------- Helper: classify question type ----------

def detect_question_type(question: str) -> str:
    """
    Very simple rule-based classifier for question types.
    Returns one of: "car_count", "trip_when", "favorite_restaurants", "generic".
    """
    q = question.lower()

    if "how many" in q and "car" in q:
        return "car_count"

    if "favorite" in q and "restaurant" in q:
        return "favorite_restaurants"

    if "when" in q and "trip" in q:
        return "trip_when"

    return "generic"


# ---------- Specialized handlers ----------

# ---- Car count ----

def extract_car_count_from_text(text: str) -> Optional[int]:
    """
    Look for patterns like '2 cars', '1 car' in the message text.
    """
    m = re.search(r"\b(\d+)\s+car", text.lower())
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def answer_car_count(member_name: str, messages: List[MemberMessage]) -> str:
    """
    Try to answer 'How many cars does X have?' for a member.
    We scan their messages from latest to oldest and look for a number before 'car(s)'.
    """
    for msg in reversed(messages):  # newest first
        count = extract_car_count_from_text(msg.text)
        if count is not None:
            return f"{member_name} has {count} car{'s' if count != 1 else ''}."

    return f"I couldn't find how many cars {member_name} has in their messages."


# ---- Trip timing ----

MONTH_PATTERN = r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?"
DATE_SLASH_PATTERN = r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"


def extract_destination_from_question(question: str) -> Optional[str]:
    """
    Try to capture the destination from phrases like 'trip to London'.
    This is intentionally simple.
    """
    m = re.search(r"trip to ([A-Za-z ]+)\??", question, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def extract_date_phrase(text: str) -> Optional[str]:
    """
    Try to find a date-like phrase in the message: 'June 5th, 2025' or '06/05/2025'.
    """
    m = re.search(MONTH_PATTERN, text)
    if m:
        return m.group(0)

    m = re.search(DATE_SLASH_PATTERN, text)
    if m:
        return m.group(0)

    return None


def answer_trip_when(question: str, member_name: str, messages: List[MemberMessage]) -> str:
    """
    Answer 'When is X planning their trip to Y?' by:
    - Detecting a destination from the question
    - Looking for the member's messages mentioning that destination
    - Extracting a date-like phrase if possible
    """
    destination = extract_destination_from_question(question)
    if not destination:
        # Fall back: just look for 'trip' in their messages
        candidate_msgs = [m for m in messages if "trip" in m.text.lower()]
        if not candidate_msgs:
            return f"I couldn't find any trip details for {member_name}."
        latest = candidate_msgs[-1]
        date_phrase = extract_date_phrase(latest.text)
        if date_phrase:
            return f"{member_name} seems to be planning a trip around {date_phrase}."
        return latest.text

    dest_lower = destination.lower()
    candidate_msgs = [m for m in messages if dest_lower in m.text.lower()]

    if not candidate_msgs:
        return f"I couldn't find any messages from {member_name} about a trip to {destination}."

    latest = candidate_msgs[-1]
    date_phrase = extract_date_phrase(latest.text)

    if date_phrase:
        return f"{member_name} is planning their trip to {destination} around {date_phrase}."
    else:
        # As a fallback, return the raw message text
        return latest.text


# ---- Favorite restaurants ----

def answer_favorite_restaurants(member_name: str, messages: List[MemberMessage]) -> str:
    """
    Look for messages mentioning 'favorite restaurant(s)' for this member.
    """
    candidates: List[str] = []
    for msg in messages:
        text_lower = msg.text.lower()
        if "favorite" in text_lower and "restaurant" in text_lower:
            candidates.append(msg.text)

    if not candidates:
        return f"I couldn't find any messages about {member_name}'s favorite restaurants."

    if len(candidates) == 1:
        return candidates[0]

    # If there are multiple, join them in a readable way
    joined = " | ".join(candidates)
    return f"{member_name}'s messages about favorite restaurants: {joined}"


# ---------- Main QA function ----------

def answer_question_baseline(question: str, messages: List[MemberMessage]) -> str:
    """
    Main QA function used by the /ask endpoint.

    Steps:
    1. Identify which member the question is about (strict).
    2. If not found, try to suggest a similar member by first name.
    3. Classify the question type.
    4. Use a specialized handler if available.
    5. Fall back to returning the latest message from that member.
    """
    if not messages:
        return "I couldn't retrieve any member messages."

    # --- 1) Strict resolution ---
    member_name = find_member_name_in_question(question, messages)

    # --- 2) If strict resolution fails, try a fuzzy suggestion ---
    requested_first_name = extract_requested_first_name(question)
    suggested_name: Optional[str] = None

    if not member_name and requested_first_name:
        suggested_name = suggest_similar_member_by_first_name(
            requested_first_name,
            messages,
        )
        if suggested_name:
            member_name = suggested_name

    if not member_name:
        # Nothing strict, nothing similar
        return "I couldn't identify which member the question is about."

    member_msgs = filter_messages_for_member(messages, member_name)
    if not member_msgs:
        return f"I couldn't find any messages for {member_name}."

    # --- 3) Classify question type and get core answer ---
    qtype = detect_question_type(question)

    if qtype == "car_count":
        core_answer = answer_car_count(member_name, member_msgs)
    elif qtype == "trip_when":
        core_answer = answer_trip_when(question, member_name, member_msgs)
    elif qtype == "favorite_restaurants":
        core_answer = answer_favorite_restaurants(member_name, member_msgs)
    else:
        # Generic fallback: latest message text
        latest_msg = member_msgs[-1]
        core_answer = latest_msg.text

    # --- 4) If we used a suggestion, wrap with clarification text ---
    if suggested_name and requested_first_name:
        return (
            f"I couldn't find any member named {requested_first_name}, "
            f"but I did find {suggested_name}. "
            f"Here is what their messages say:\n\n{core_answer}"
        )

    # Normal path (exact match, e.g., Layla, Sophia, etc.)
    return core_answer
