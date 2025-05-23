from datetime import datetime, timedelta, timezone

import jwt  # Changed from from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.token_schema import TokenData

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# JWT Creation
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES  #
        )
    # PyJWT expects 'exp' to be a direct part of the payload
    payload = {
        "exp": expire,
        "sub": to_encode.get("sub"),
    }  # Add other claims from 'to_encode' as needed

    # Add any other claims from 'to_encode' to the payload
    # For example, if 'to_encode' could have more than just 'sub':
    # payload.update({k: v for k, v in to_encode.items() if k not in ['sub']})

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,  #
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],  #
        )
        username: str | None = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)  #
    # PyJWT raises specific exceptions for different error conditions
    except jwt.ExpiredSignatureError:
        # Handle expired token, e.g., return None or raise a custom exception
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        # Handle other invalid token errors
        print("Invalid token")
        return None
    except Exception as e:  # Generic catch for other potential jwt errors
        print(f"An unexpected error occurred during token decoding: {e}")
        return None

