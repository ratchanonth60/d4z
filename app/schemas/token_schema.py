from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    # สามารถเพิ่ม fields อื่นๆ ที่คุณต้องการเก็บใน token payload ได้
    # เช่น user_id: Optional[int] = None
