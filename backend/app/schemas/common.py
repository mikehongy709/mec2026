# app/schemas/common.py

from pydantic import BaseModel

class MessageResponse(BaseModel):
    message: str

class SuccessResponse(BaseModel):
    success: bool = True