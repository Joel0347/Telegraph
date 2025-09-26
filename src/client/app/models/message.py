from pydantic import BaseModel, Field
from datetime import datetime

class Message(BaseModel):
    from_: str = Field(..., alias="from", min_length=1)
    to: str = Field(..., min_length=1)
    text: str
    timestamp: datetime
    read: bool

    model_config = {
        "from_attributes": True,
        "extra": "forbid",
        "populate_by_name": True,
    }

    # def to_json_dict(self) -> dict:
    #     return {
    #         "from": self.from_,
    #         "to": self.to,
    #         "text": self.text,
    #         "timestamp": self.timestamp.isoformat(),
    #         "read": self.read
    #     }

    # @classmethod
    # def from_json_dict(cls, d: dict):
    #     return cls.model_validate(d)
