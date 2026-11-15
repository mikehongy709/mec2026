from pydantic import BaseModel

class UserResponse(BaseModel):

    id: int

    username: str

    email: str

    avatar_url: str | None = None

    bio: str | None = None

    class Config:
        from_attributes = True

    
class UserUpdateRequest(BaseModel):

    username: str | None = None

    bio: str | None = None

    avatar_url: str | None = None