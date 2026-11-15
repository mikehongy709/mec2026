from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.users import User

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest
)

from app.repositories.users_repositories import UserRepository

from app.core.security import (
    hash_password,
    verify_password,
    create_token
)



class AuthService:


    def __init__(
        self,
        db:Session
    ):

        self.repo = UserRepository(db)



    def register(
        self,
        data:RegisterRequest
    ):


        existing = self.repo.get_by_email(
            data.email
        )


        if existing:

            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

        print("Creating user with email:", data.email)
        user = User(

            username=data.username,

            email=data.email,

            password=hash_password(
                data.password
            )
        )


        return self.repo.create(
            user
        )



    def login(
        self,
        data:LoginRequest
    ):


        user = self.repo.get_by_email(
            data.email
        )


        if user is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid email"
            )


        if not verify_password(
            data.password,
            user.password
        ):

            raise HTTPException(
                status_code=401,
                detail="Wrong password"
            )


        token = create_token(
            user
        )


        return token