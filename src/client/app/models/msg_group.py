from pydantic import BaseModel, Field
from models.message import Message


class MessageGroup(BaseModel):
    name: str = Field(..., min_length=1)
    messages: list[Message]

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }