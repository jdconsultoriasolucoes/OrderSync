
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import SessionLocal
from models.usuario import UsuarioModel
from core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from core.deps import get_current_user
from schemas.usuario import Token

router = APIRouter(prefix="/token", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate User
    # Authenticate User (Case Insensitive)
    user = db.query(UsuarioModel).filter(UsuarioModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.ativo:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Create Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.funcao},
        expires_delta=access_token_expires
    )
    

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "funcao": user.funcao,
        "nome": user.nome,
        "reset_senha_obrigatorio": user.reset_senha_obrigatorio or False
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    current_user: UsuarioModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Renova o token de acesso para o usuário logado.
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email, "role": current_user.funcao},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "funcao": current_user.funcao,
        "nome": current_user.nome,
        "reset_senha_obrigatorio": current_user.reset_senha_obrigatorio or False
    }

from schemas.usuario import UsuarioForgotPassword, UsuarioResetSenha
from services.email_service import enviar_email_recuperacao_senha
from jose import jwt, JWTError
from core.security import SECRET_KEY, ALGORITHM, get_password_hash

# Configurações do Token de Reset
RESET_TOKEN_EXPIRE_MINUTES = 15

@router.post("/forgot-password")
def forgot_password(data: UsuarioForgotPassword, db: Session = Depends(get_db)):
    """
    Gera um token de recuperação e envia por e-mail.
    Sempre retorna 200 para não vazar existência de e-mails.
    """
    user = db.query(UsuarioModel).filter(UsuarioModel.email == data.email).first()
    
    if user and user.ativo:
        # Gerar Token Específico para Reset
        expires = timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        reset_token = create_access_token(
            data={"sub": user.email, "scope": "reset_password"},
            expires_delta=expires
        )
        
        # Link do Frontend (ajustar conforme ambiente)
        # Em dev: http://localhost:5500/public/login/reset.html?token=...
        # Em prod: https://seu-app.com/public/login/reset.html?token=...
        
        # Tentativa de descobrir a URL base via headers, ou fallback
        # Simplificação: enviar o link relativo ou fixo se soubermos
        # Para garantir, vou usar uma base genérica. O ideal é ter uma VAR de ambiente FRONTEND_URL.
        try:
            # Pega o host atual
             # Se rodando localmente, assumimos port 5500 ou 3000 para o front
            base_url = "http://127.0.0.1:5500" # Fallback Dev
            
            # Se a requisição vem de uma origem conhecida, usamos ela
            # Mas aqui no backend, request.base_url aponta pro backend.
            # Vamos assumir que o frontend está servido estaticamente ou em porta conhecida.
            # Melhor: Usar Referer ou Origin se disponível
            
            # PROVISÓRIO:
            link = f"{base_url}/public/login/reset.html?token={reset_token}"
            
            enviar_email_recuperacao_senha(db, user.email, link)
            
        except Exception as e:
            print(f"Erro no forgot_password: {e}")

    return {"message": "Se o e-mail existir, um link de recuperação foi enviado."}

@router.post("/reset-password")
def reset_password(data: UsuarioResetSenha, db: Session = Depends(get_db)):
    """
    Valida token e atualiza senha.
    """
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        scope = payload.get("scope")
        
        if email is None or scope != "reset_password":
            raise HTTPException(status_code=400, detail="Token inválido ou expirado")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
        
    user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    # Atualizar senha
    user.senha_hash = get_password_hash(data.senha_nova)
    db.commit()
    
    return {"message": "Senha atualizada com sucesso."}
