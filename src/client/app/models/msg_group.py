from pydantic import BaseModel, Field, model_validator
from models.message import Message


class MessageGroup(BaseModel):
    name: str = Field(..., min_length=1)
    synchronized: bool | None = Field(default=None)
    messages: list[Message]

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }
    
    @model_validator(mode="after")
    def set_default_synchronized(self):
        if self.synchronized is None:
            self.synchronized = True
        return self    