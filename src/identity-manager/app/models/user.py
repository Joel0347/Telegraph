from pydantic import BaseModel, Field
from typing import Annotated, Literal
from datetime import datetime


class User(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ip: str | None = None
    port: Annotated[int, Field(ge=0, le=65535)] | None = None
    status: Literal["online", "offline"]
    last_seen: datetime | None = None

    model_config = {
        "from_attributes": True,
        "extra": "forbid",
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
