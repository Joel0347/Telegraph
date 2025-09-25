from pydantic import BaseModel, Field
from typing import Annotated


class User(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ip: str | None = None
    port: Annotated[int, Field(ge=0, le=65535)] | None = None

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }
