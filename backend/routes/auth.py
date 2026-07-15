import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from database.connection import db
from database.schema import create_user, get_user_by_email
from routes.schemas import LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_TO_A_RANDOM_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenData(BaseModel):
    email: Optional[str] = None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if not isinstance(email, str):
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    if not token_data.email:
        raise credentials_exception

    user = get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    return {"email": user["email"], "id": str(user["_id"])}


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    if get_user_by_email(request.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = hash_password(request.password)
    create_user(
        {
            "email": request.email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
        }
    )

    access_token = create_access_token({"sub": request.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    hashed_password = user.get("hashed_password") or user.get("password")
    if not hashed_password or not verify_password(request.password, hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token({"sub": request.email})
    return {"access_token": access_token, "token_type": "bearer"}
