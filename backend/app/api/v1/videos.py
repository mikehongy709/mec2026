from typing import List

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form
)

from sqlalchemy.orm import Session


from app.core.database import get_db
from app.core.security import verify_token

from app.models.users import User


from app.services.videos_service import VideoService



router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)



@router.get(
    "/temp",
    response_model=VideoResponse
)
def get_temperature(
    title:str=Form(...),
    user_id:int=Depends(verify_token),
    db:Session=Depends(get_db)
):

    service=VideoService(db)


    return service.upload_video(
        title,
        file,
        user_id
    )



@router.post(
    "/",
    response_model=list[VideoResponse]
)
def get_videos(
    db:Session=Depends(get_db)
):

    service=VideoService(db)


    return service.get_all_videos()



@router.get(
    "/my",
    response_model=list[VideoResponse]
)
def get_my_videos(
    user_id:int = Depends(verify_token),
    db:Session=Depends(get_db)
):

    service=VideoService(db)


    return service.get_my_videos(
        user_id
    )



@router.get(
    "/detail/{video_id}",
    response_model=VideoDetailResponse
)
def detail(
    video_id:int,
    db:Session=Depends(get_db)
):

    service=VideoService(db)


    return service.get_video_detail(
        video_id
    )



@router.put(
    "/{video_id}",
    response_model=VideoDetailResponse
)
def update(
    video_id:int,
    request:VideoUpdateRequest,
    user_id:int = Depends(verify_token),
    db:Session=Depends(get_db)
):

    service=VideoService(db)


    return service.update_video(
        video_id,
        request,
        user_id
    )



@router.delete(
    "/{video_id}"
)
def delete(
    video_id:int,
    user_id:int = Depends(verify_token),
    db:Session=Depends(get_db)
):

    service=VideoService(db)

    service.delete_video(
        video_id,
        user_id
    )


    return {
        "message":"deleted"
    }