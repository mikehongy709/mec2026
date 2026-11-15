from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.core.database import get_db

from app.models.users import User

from app.services.users_service import UserService

from app.schemas.users import UserResponse, UserUpdateRequest



router = APIRouter()


@router.get(
        "/me",
        response_model=UserResponse
            )
def get_me(
    user_id : int = Depends(verify_token),
    db: Session = Depends(get_db)
):

    service = UserService(db)

    return service.get_user_by_id(
        user_id
    )

@router.put(
    "/me",
    response_model=UserResponse
)
def update_me(
    request:UserUpdateRequest,
    user_id:int = Depends(verify_token),
    db:Session = Depends(get_db)
):

    service = UserService(db)


    return service.update_profile(
        user_id,
        request
    )