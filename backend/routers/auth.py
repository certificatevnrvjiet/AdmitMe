from fastapi import APIRouter, Depends, HTTPException, status
import bcrypt
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from services.auth_service import authenticate_user, create_access_token, get_current_user, oauth2_scheme
from models.UserModel import UserCreate, UserUpdate, PasswordChange
from database import supabase
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

def _ensure_admin(current_user: dict):
    if (current_user.get("role") or "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can access user management",
        )

def _issue_token(form_data: OAuth2PasswordRequestForm):
    user_result = authenticate_user(form_data.username, form_data.password)
    if "error" in user_result:
        if user_result.get("system_error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable",
            )
        raise HTTPException( 
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = user_result['user']
    normalized_email = (user["email"] or "").strip().lower()
    normalized_role = (user["dept"] or "").strip().lower()
    token_data = {
        "sub": normalized_email,
        "role": normalized_role,
        "dept_scope": normalized_role,
        "token_version": 1,
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "role": normalized_role}


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return _issue_token(form_data)


@router.post("/auth/login")
def login_standard(form_data: OAuth2PasswordRequestForm = Depends()):
    return _issue_token(form_data)

@router.get("/api/verify-token")
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check expiration
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        
        # Return user details along with validation status
        return {
            "valid": True,
            "user": payload.get("sub"),
            "role": payload.get("role"),
            "expires": datetime.fromtimestamp(exp).isoformat()
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

@router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"User": current_user['username'], "role": current_user['role']}


@router.get("/auth/me")
def read_users_me_standard(current_user: dict = Depends(get_current_user)):
    return {
        "user": current_user["username"],
        "role": current_user["role"],
        "rights": current_user.get("rights"),
    }

@router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Get all users - Admin only"""
    _ensure_admin(current_user)
    
    try:
        response = supabase.table("users").select("id, email, dept, rights").execute()
        return {"users": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    """Create a new user - Admin only"""
    _ensure_admin(current_user)
    
    try:
        normalized_email = (str(user_data.email) or "").strip().lower()

        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", normalized_email).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user (hash password)
        pwd_bytes = user_data.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(pwd_bytes, salt)
        
        user_dict = user_data.model_dump()
        user_dict["email"] = normalized_email
        user_dict["dept"] = (user_dict.get("dept") or "").strip().lower()
        user_dict['password'] = hashed_password.decode('utf-8')
        
        response = supabase.table("users").insert(user_dict).execute()
        
        if response.data:
            created_user = response.data[0]
            return {
                "message": "User created successfully",
                "user": {
                    "id": created_user["id"],
                    "email": created_user["email"],
                    "dept": created_user["dept"],
                    "rights": created_user["rights"]
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)

    payload = {k: v for k, v in user_data.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    if "email" in payload:
        payload["email"] = (str(payload["email"]) or "").strip().lower()
    if "dept" in payload:
        payload["dept"] = (str(payload["dept"]) or "").strip().lower()

    if "password" in payload:
        pwd_bytes = payload["password"].encode("utf-8")
        payload["password"] = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")

    try:
        response = (
            supabase.table("users")
            .update(payload)
            .eq("id", user_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        updated_user = response.data[0]
        safe_user = {
            "id": updated_user.get("id"),
            "email": updated_user.get("email"),
            "dept": updated_user.get("dept"),
            "rights": updated_user.get("rights"),
        }
        return {"message": "User updated successfully", "user": safe_user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/change-password")
async def change_password(user_id: str, payload: PasswordChange, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed = bcrypt.hashpw(payload.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    try:
        response = (
            supabase.table("users")
            .update({"password": hashed})
            .eq("id", user_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)

    # Prevent admin from deleting own account accidentally.
    if current_user.get("id") == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    try:
        response = (
            supabase.table("users")
            .delete()
            .eq("id", user_id)
            .execute()
        )
        return {"message": "User deleted successfully", "deleted": bool(response.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
