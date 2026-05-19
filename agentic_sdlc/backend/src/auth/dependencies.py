import jwt
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User
from src.auth.service import decode_token

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError
        payload = decode_token(token)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise ValueError
        return user
    except (jwt.PyJWTError, ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
