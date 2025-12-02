from pydantic import BaseModel


class Log(BaseModel):
    term: int = 0
    index: int = -1
    op: str | None = None
    args: dict | None = None
    applied: bool = False
