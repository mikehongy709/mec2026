from fastapi import HTTPException, UploadFile

from sqlalchemy.orm import Session

from app.models.videos import Video
from app.models.users import User

from backend.app.repositories.status_repositories import VideoRepository

from app.schemas.videos import VideoUpdateRequest

from app.services.storage_service import StorageService



class VideoService:


    def __init__(
        self,
        db:Session
    ):

        self.db=db

        self.repo=VideoRepository(
            db
        )

        self.storage=StorageService()



    def upload_video(
        self,
        title:str,
        file:UploadFile,
        user_id:int
    ):


        result = self.storage.save_video(
            file
        )


        video = Video(
            title=title,

            filename=result["filename"],

            url=result["url"],

            owner_id=user_id
        )


        self.repo.create(
            video
        )


        self.db.commit()

        self.db.refresh(video)


        return video



    def get_all_videos(
        self,
        offset:int=0,
        limit:int=20
    ):

        return self.repo.get_all(
            offset,
            limit
        )



    def get_my_videos(
        self,
        user_id:int
    ):

        return self.repo.get_by_owner(
            user_id
        )



    def get_video_detail(
        self,
        video_id:int
    ):

        video = self.repo.get_by_id(
            video_id
        )


        if video is None:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )


        video.views += 1


        self.db.commit()

        self.db.refresh(video)


        return video



    def update_video(
        self,
        video_id:int,
        request:VideoUpdateRequest,
        user_id:int
    ):


        video = self.repo.get_by_id(
            video_id
        )


        if video is None:
            raise HTTPException(
                404,
                "Video not found"
            )


        if video.owner_id != user_id:
            raise HTTPException(
                403,
                "Permission denied"
            )


        data=request.model_dump(
            exclude_unset=True
        )


        video=self.repo.update(
            video,
            data
        )


        self.db.commit()

        self.db.refresh(video)


        return video



    def delete_video(
        self,
        video_id:int,
        user_id:int
    ):


        video=self.repo.get_by_id(
            video_id
        )


        if video is None:
            raise HTTPException(
                404,
                "Video not found"
            )


        if video.owner_id != user_id:

            raise HTTPException(
                403,
                "Permission denied"
            )


        self.repo.delete(
            video
        )


        self.db.commit()