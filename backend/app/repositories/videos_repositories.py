from sqlalchemy.orm import Session

from app.models.status import Status


class StatusRepository:


    def __init__(
        self,
        db: Session
    ):
        self.db = db



    # CREATE

    def create(
        self,
        status: Status
    ):

        self.db.add(status)

        self.db.flush()

        return status



    # READ ONE

    def get_by_id(
        self,
        stats_id:int
    ):

        return (
            self.db
            .query(Status)
            .filter(
                Status.id == stats_id
            )
            .first()
        )



    # READ ALL

    def get_all(
        self,
    ):

        return (
            self.db
            .query(Status)
            .order_by(
                Status.created_at.desc()
            )
            .all()
        )



   