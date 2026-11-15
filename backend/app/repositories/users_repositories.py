from sqlalchemy.orm import Session

from app.models.users import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db


    # CREATE
    def create(
        self,
        user: User
    ):
        self.db.add(user)

        self.db.flush()

        return user



    # READ
    def get_by_id(
        self,
        user_id: int
    ):

        return (
            self.db
            .query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )


    def get_by_email(
        self,
        email: str
    ):

        return (
            self.db
            .query(User)
            .filter(
                User.email == email
            )
            .first()
        )


    def get_by_username(
        self,
        username: str
    ):

        return (
            self.db
            .query(User)
            .filter(
                User.username == username
            )
            .first()
        )



    # READ ALL
    def get_all(
        self,
        offset: int = 0,
        limit: int = 20
    ):

        return (
            self.db
            .query(User)
            .offset(offset)
            .limit(limit)
            .all()
        )



    # UPDATE
    def update(
        self,
        user: User,
        data: dict
    ):

        for key, value in data.items():

            if value is not None:
                setattr(
                    user,
                    key,
                    value
                )

        self.db.flush()

        return user



    # DELETE
    def delete(
        self,
        user: User
    ):

        self.db.delete(user)

        self.db.flush()