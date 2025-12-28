
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from database import SessionLocal
from models.usuario import UsuarioModel
from schemas.usuario import UsuarioCreate, UsuarioPublic, UsuarioUpdateSenha, UsuarioResetSenha, UsuarioUpdate
from core.security import get_password_hash, SECRET_KEY, ALGORITHM, verify_password

# Dependency for Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user_role(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role: str = payload.get("role")
        if role is None:
            raise credentials_exception
        return role
    except JWTError:
        raise credentials_exception

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
    return user

# Router
router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.post("/", response_model=UsuarioPublic)
def create_user(
    usuario: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_role: str = Depends(get_current_user_role)
):
    # Only Admin or Gerente can create users
    if current_role not in ["admin", "gerente"]:
         raise HTTPException(status_code=403, detail="Not authorized to create users")

    # Check existing
    if db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(usuario.senha)
    db_user = UsuarioModel(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hashed_pw,
        funcao=usuario.funcao,
        ativo=usuario.ativo
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UsuarioPublic])
def list_users(
    db: Session = Depends(get_db),
    current_role: str = Depends(get_current_user_role)
):
    if current_role not in ["admin", "gerente"]:
         raise HTTPException(status_code=403, detail="Not authorized to list users")
         
    return db.query(UsuarioModel).all()

@router.post("/me/senha")
def alterar_minha_senha(
    dados: UsuarioUpdateSenha,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Verify old password
    if not verify_password(dados.senha_antiga, current_user.senha_hash):
        raise HTTPException(status_code=400, detail="Senha antiga incorreta")
    
    # Update
    current_user.senha_hash = get_password_hash(dados.senha_nova)
    current_user.data_atualizacao = datetime.now() # if not auto
    db.commit()
    return {"message": "Senha alterada com sucesso"}

@router.post("/{user_id}/reset-senha")
def resetar_senha_usuario(
    user_id: int,
    dados: UsuarioResetSenha,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Only Admin
    if current_user.funcao != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem resetar senhas")
    
    target_user = db.query(UsuarioModel).filter(UsuarioModel.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    target_user.senha_hash = get_password_hash(dados.senha_nova)
    db.commit()
    return {"message": f"Senha do usuário {target_user.email} resetada com sucesso"}

@router.put("/{user_id}", response_model=UsuarioPublic)
def update_user(
    user_id: int,
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Only Admin
    if current_user.funcao != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem editar usuários")

    user = db.query(UsuarioModel).filter(UsuarioModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if dados.nome is not None: user.nome = dados.nome
    if dados.email is not None: user.email = dados.email
    if dados.funcao is not None: user.funcao = dados.funcao
    if dados.ativo is not None: user.ativo = dados.ativo

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Only Admin
    if current_user.funcao != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir usuários")

    user = db.query(UsuarioModel).filter(UsuarioModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir sua própria conta")

    db.delete(user)
    db.commit()
    return {"message": "Usuário excluído com sucesso"}
