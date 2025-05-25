from datetime import datetime, timedelta, timezone
import jwt  # PyJWT
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.token_schema import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(
    data: dict, expires_delta: timedelta, token_type: str = "access"
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    # เพิ่ม token_type เข้าไปใน payload เพื่อแยกแยะระหว่าง access และ refresh token
    # และสามารถใช้ subject (sub) สำหรับ username หรือ user_id ได้
    payload = {"exp": expire, "sub": to_encode.get("sub"), "type": token_type}
    if "user_id" in to_encode:  # Optional: if you want user_id in token
        payload["user_id"] = to_encode.get("user_id")

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,  #
    )
    return encoded_jwt


def create_access_token(data: dict) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)  #
    return _create_token(data=data, expires_delta=expires_delta, token_type="access")


def create_refresh_token(data: dict) -> str:
    expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)  #
    return _create_token(data=data, expires_delta=expires_delta, token_type="refresh")


def decode_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        token_data_obj = TokenData(username=username, type=token_type)

        return token_data_obj if username else None

    except jwt.ExpiredSignatureError:
        # Log or handle expired token specifically if needed
        # For JWTBearer, it will be caught and re-raised as AuthenticationError
        raise  # Re-raise specific PyJWT errors to be caught by JWTBearer
    except jwt.InvalidTokenError:
        # Log or handle other invalid token errors
        raise  # Re-raise
    except Exception:
        # Log unexpected errors
        raise  # Re-raise
