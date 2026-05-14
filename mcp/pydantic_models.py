from typing import List, Optional
from pydantic import BaseModel, Field

class ColumnMetadata(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class TableReference(BaseModel):
    namespace: str
    table: str
    identifier: str

class TableMetadata(BaseModel):
    namespace: str
    table: str
    identifier: str
    description: Optional[str] = None
    properties: dict[str, str]
    columns: List[ColumnMetadata]

class SqlExecutionResult(BaseModel):
    statement_type: str
    columns: List[str] = Field(default_factory=list)
    rows: List[dict] = Field(default_factory=list)
    row_count: int
    truncated: bool = False
