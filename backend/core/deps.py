
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

class RequirePermission:
    def __init__(self, modulo: str, acao: str):
        self.modulo = modulo
        self.acao = acao

    def __call__(self, current_user: UsuarioModel = Depends(get_current_user), db: Session = Depends(get_db)):
        # Admin bypass
        if current_user.perfil and current_user.perfil.is_system and current_user.perfil.nome == "admin":
            return True
        if current_user.funcao == "admin": # retrocompatibilidade
            return True
            
        if not current_user.perfil:
            raise HTTPException(status_code=403, detail="Usuário sem perfil de acesso definido.")

        from models.perfil import PerfilPermissaoModel
        permissao = db.query(PerfilPermissaoModel).filter_by(
            perfil_id=current_user.perfil.id, 
            modulo=self.modulo
        ).first()

        if not permissao:
            raise HTTPException(status_code=403, detail=f"Sem acesso ao módulo {self.modulo}.")

        tem_acesso = getattr(permissao, f"pode_{self.acao}", False)
        if not tem_acesso:
            raise HTTPException(status_code=403, detail=f"Permissão negada para a ação '{self.acao}' no módulo '{self.modulo}'.")
        
        return True
