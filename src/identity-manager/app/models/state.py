from pydantic import BaseModel


class State(BaseModel):
    current_term: int = 0
    voted_for: str | None = None
    current_leader: str | None = None
    commit_index: int = -1
    last_applied: int = -1

