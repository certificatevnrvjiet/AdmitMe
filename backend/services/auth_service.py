import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from database import supabase
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_user(username: str, password: str):
    try:
        # Fetch user with matching email
        response = supabase.table("users").select("*").eq("email", username).single().execute()

        if response.data is None:
            return {"error": "User not found"}

        user = response.data
        # Check password (support both bcrypt hash and plain text for legacy/dev)
        try:
            if not bcrypt.checkpw(password.encode(), user["password"].encode()):
                return {"error": "Invalid credentials"}
        except ValueError:
            # Fallback for plain text passwords
            if password != user["password"]:
                return {"error": "Invalid credentials"}

        return {"user": {
            "id": user["id"],
            "email": user["email"],
            "dept": user["dept"],
        }}

    except Exception as e:
        return {"error": str(e)}

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
        username = payload.get("sub")
        role = payload.get("role")
        
        if username is None or role is None:
            raise credentials_exception
            
        response = supabase.table("users").select("*").eq("email", username).single().execute()
        rights = response.data.get('rights')
        
    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception
        
    return {"username": username, "role": role, "rights": rights}
