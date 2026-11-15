from pydantic import BaseModel
from app.schemas.users import UserResponse

class VideoResponse(BaseModel):

    id: int

    title: str

    thumbnail_url: str | None = None

    url: str

    views: int=0

    class Config:
        from_attributes = True

from datetime import datetime

class VideoDetailResponse(BaseModel):

    description: str | None = None

    url: str

    views: int

    created_at: datetime

    owner: UserResponse

    class Config:
        from_attributes = True

class VideoUpdateRequest(BaseModel):

    title: str

    description: str | None = None

class VideoListResponse(BaseModel):

    items: list[VideoResponse]

    page: int

    size: int

    total: int