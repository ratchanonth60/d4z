from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Type variable T will be replaced by the actual data type
DataT = TypeVar("DataT")


class PaginationInfo(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int


class BaseResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[DataT] = None
    pagination: Optional[PaginationInfo] = None


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    type: Optional[str] = None


class ErrorResponse(BaseResponse[None]):  # Data is None for error responses
    success: bool = Field(
        default=False,
    )  # Override success to be False and const
    errors: Optional[List[ErrorDetail]] = None
    pagination: Optional[PaginationInfo] = None
