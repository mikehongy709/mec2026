from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.models.users import User

SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"

security = HTTPBearer()

def create_token(user):

    payload={
        "sub":str(user.id)
    }


    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm="HS256"
    )


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        id = payload.get("sub")

        if id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
        return id

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
def hash_password(password:str):

    password_bytes = password.encode("utf-8")

    if len(password_bytes)>72:
        raise ValueError(
            "Password too long"
        )

    salt=bcrypt.gensalt()

    hashed=bcrypt.hashpw(
        password_bytes,
        salt
    )

    return hashed.decode()



def verify_password(
    password:str,
    hashed:str
):

    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )