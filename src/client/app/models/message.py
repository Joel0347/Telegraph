from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class Message(BaseModel):
    from_: str = Field(..., alias="from", min_length=1)
    to: str = Field(..., min_length=1)
    text: str
    timestamp: datetime
    read: bool
    status: Literal["ok", "pending"]

    model_config = {
        "from_attributes": True,
        "extra": "forbid",
        "populate_by_name": True,
    }
