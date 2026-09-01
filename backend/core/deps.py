
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import SessionLocal
from models.usuario import UsuarioModel
from core.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
    if user is None:
        raise credentials_exception
    
    # Injeta contexto para Row-Level Security (RLS) no PostgreSQL
    from sqlalchemy import text
    try:
        db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": str(user.id)})
        db.execute(text("SET LOCAL app.current_user_role = :role"), {"role": str(user.funcao)})
    except Exception as e:
        # Passa silenciosamente caso o banco não seja Postgres (ex: fallback SQLite dev)
        pass
        
    return user

async def get_current_user_optional(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token", auto_error=False)), db: Session = Depends(get_db)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email:
            user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
            if user:
                from sqlalchemy import text
                try:
                    db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": str(user.id)})
                    db.execute(text("SET LOCAL app.current_user_role = :role"), {"role": str(user.funcao)})
                except Exception:
                    pass
                return user
    except Exception:
        pass
    return None
