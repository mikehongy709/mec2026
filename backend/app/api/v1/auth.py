from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse
)
from app.services.auth_service import AuthService



router = APIRouter()


@router.post(
    "/register"
)
def register(
    data:RegisterRequest,
    db:Session=Depends(get_db)
):

    service = AuthService(db)


    service.register(
        data
    )


    return {
        "message":
        "Registered successfully"
    }



@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    data:LoginRequest,
    db:Session=Depends(get_db)
):

    service = AuthService(db)


    token = service.login(
        data
    )


    return {
        "access_token":token
    }