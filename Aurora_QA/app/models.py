from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MemberMessage(BaseModel):
    """
    Internal representation of a member message.

    NOTE: We will adjust the fields once we see the real /messages response.
    """
    member_id: Optional[str] = None
    member_name: Optional[str] = None
    text: str
    created_at: Optional[datetime] = None
