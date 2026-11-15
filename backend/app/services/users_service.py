from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.repositories.users_repositories import UserRepository
from app.schemas.users import UserUpdateRequest


class UserService:


    def __init__(
        self,
        db: Session
    ):

        self.repo = UserRepository(db)
        self.db = db



    def get_user_by_id(
        self,
        user_id:int
    ):

        user = self.repo.get_by_id(
            user_id
        )


        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )


        return user



    def update_user(
        self,
        user_id:int,
        request:UserUpdateRequest
    ):

        user = self.repo.get_by_id(
            user_id
        )


        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )


        data = request.model_dump(
            exclude_unset=True
        )


        user = self.repo.update(
            user,
            data
        )


        self.db.commit()
        self.db.refresh(user)


        return user



    def delete_account(
        self,
        user_id:int
    ):

        user = self.repo.get_by_id(
            user_id
        )


        if user is None:
            raise HTTPException(
                status_code=404
            )


        self.repo.delete(user)


        self.db.commit()