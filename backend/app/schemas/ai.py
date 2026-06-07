from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AIChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None

class AIChatResponse(BaseModel):
    response: str
