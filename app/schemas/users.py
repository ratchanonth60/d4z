from enum import Enum
from typing import Optional

from pydantic import BaseModel


class UserFilterParams(BaseModel):
    username_contains: Optional[str] = None
    email_equals: Optional[str] = None
    is_active: Optional[bool] = None


class UserSortByField(str, Enum):
    USERNAME = "username"
    ID = "id"
    EMAIL = "email"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"
