from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Standard API response structure."""
    success: bool
    message: str
    code: str
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = None

    @classmethod
    def ok(cls, data: T = None, message: str = "Success", code: str = "SUCCESS", meta: dict = None):
        return cls(success=True, message=message, code=code, data=data, meta=meta)

    @classmethod
    def error(cls, message: str = "Error", code: str = "ERROR", data: Any = None, meta: dict = None):
        return cls(success=False, message=message, code=code, data=data, meta=meta)
