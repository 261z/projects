from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..db.schemas import AuthResponse, Credentials, UserResponse
from ..services.auth_service import authenticate_user, create_access_token, decode_access_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = decode_access_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: Credentials) -> UserResponse:
    try:
        user_id = register_user(payload.username, payload.password)
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from exc
        raise
    return UserResponse(id=user_id, username=payload.username)


@router.post("/login", response_model=AuthResponse)
def login(payload: Credentials) -> AuthResponse:
    user = authenticate_user(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return AuthResponse(access_token=create_access_token(user["id"], user["username"]), username=user["username"])


@router.post("/logout")
def logout(_: dict = Depends(current_user)) -> dict[str, str]:
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(current_user)) -> UserResponse:
    return UserResponse(**user)
