import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from database import supabase
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from services.catalog_service import normalize_branch_code

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
logger = logging.getLogger(__name__)

def _normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()

def _normalize_role(value: str | None) -> str:
    return (value or "").strip().lower()

def authenticate_user(username: str, password: str):
    try:
        normalized_username = _normalize_email(username)
        # Fetch user by email
        response = (
            supabase.table("users")
            .select("*")
            .eq("email", normalized_username)
            .limit(1)
            .execute()
        )

        if not response.data:
            return {"error": "Invalid credentials"}

        user = response.data[0]

        stored_password = user.get("password")
        if not stored_password:
            return {"error": "Invalid credentials"}

        # Verify bcrypt hash
        if not bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
            return {"error": "Invalid credentials"}

        return {
            "user": {
                "id": user["id"],
                "email": _normalize_email(user["email"]),
                "dept": _normalize_role(user["dept"]),
            }
        }

    except Exception as exc:
        logger.exception("Authentication lookup failed for username=%s", (username or "").strip())
        return {"error": "Authentication service unavailable", "system_error": True}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = _normalize_email(payload.get("sub"))
        role = _normalize_role(payload.get("role"))
        
        if username is None or role is None:
            raise credentials_exception
            
        response = supabase.table("users").select("*").eq("email", username).single().execute()
        if not response.data:
            raise credentials_exception

        db_user = response.data
        rights = db_user.get("rights") or "Read Only"
        role = _normalize_role(db_user.get("dept") or role)
        user_id = db_user.get("id")
        
    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception
        
    return {"id": user_id, "username": username, "role": role, "rights": rights}

def is_student_user(current_user: dict[str, Any]) -> bool:
    return _normalize_role(current_user.get("role")) == "student"

def is_student_owner(current_user: dict[str, Any], student: dict[str, Any]) -> bool:
    username = _normalize_email(current_user.get("username"))
    student_email = _normalize_email((student or {}).get("student_email"))
    return bool(username and student_email and username == student_email)

def _normalized_branch(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    try:
        return normalize_branch_code(text).lower()
    except ValueError:
        return text.lower()

def can_access_student_record(current_user: dict[str, Any], student: dict[str, Any]) -> bool:
    role = _normalize_role(current_user.get("role"))
    if role == "admin":
        return True
    if role == "student":
        return is_student_owner(current_user, student)

    role_branch = _normalized_branch(role)
    student_branch = _normalized_branch((student or {}).get("branch_code"))
    student_degree = _normalized_branch((student or {}).get("degree_code"))
    return role_branch in {student_branch, student_degree}
