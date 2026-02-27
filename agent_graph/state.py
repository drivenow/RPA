from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class GraphState(BaseModel):
    """共享状态结构，节点间传递核心字段和扩展上下文。"""

    url: str
    raw_html: Optional[str] = None
    clean_html: Optional[str] = None
    plain_text: Optional[str] = None
    summary: Optional[str] = None
    error_node: Optional[str] = None
    error_message: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)

