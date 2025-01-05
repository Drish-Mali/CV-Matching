from typing import List, Optional, Dict
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class PostData(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: int = 1
    stop: Optional[List[str]] = None
    stream: bool = False
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
