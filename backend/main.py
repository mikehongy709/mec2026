from fastapi import FastAPI
from app.api.v1.auth import router as auth_router
from app.api.v1.user import router as user_router
from app.api.v1.videos import router as video_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.core.database import Base
from fastapi.staticfiles import StaticFiles



app = FastAPI(
    title="Video Platform API"
)

Base.metadata.create_all(bind=engine)


app.include_router(
    auth_router,
    prefix="/auth"
)

app.include_router(user_router, prefix="/users")

app.include_router(video_router)

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


@app.get("/")
def home():

    return {
        "message":
        "Backend running"
    }