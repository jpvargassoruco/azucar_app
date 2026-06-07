from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserUpdateAI, AITestRequest
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user in the system."""
    result = await db.execute(select(User).filter(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )
    
    db_user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate a user using email and password, returning a JWT access token."""
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo electrónico o contraseña incorrectos."
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario está inactivo."
        )
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the current logged-in user profile details."""
    return current_user

@router.put("/me/ai-settings", response_model=UserResponse)
async def update_ai_settings(
    settings_in: UserUpdateAI,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's personal AI configuration."""
    if settings_in.ai_provider is not None:
        current_user.ai_provider = settings_in.ai_provider
        
    if settings_in.ai_model is not None:
        current_user.ai_model = settings_in.ai_model
        
    if settings_in.ai_base_url is not None:
        current_user.ai_base_url = settings_in.ai_base_url
        
    if settings_in.ai_api_key is not None:
        key_value = settings_in.ai_api_key.strip()
        if key_value == "":
            current_user.ai_api_key = None
        elif key_value.startswith("***") or (current_user.ai_api_key and key_value == current_user.ai_api_key_masked):
            # Keep the existing key if they submit the masked representation
            pass
        else:
            current_user.ai_api_key = key_value
            
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/test-ai")
async def test_ai_connection(
    test_in: AITestRequest,
    current_user: User = Depends(get_current_user)
):
    """Test AI provider connection with custom settings before saving."""
    provider = test_in.ai_provider
    api_key = test_in.ai_api_key
    model = test_in.ai_model
    
    # Resolve base URL
    base_url = test_in.ai_base_url
    if not base_url:
        if provider == "kimi":
            base_url = "https://api.moonshot.cn/v1"
        else:
            base_url = "https://openrouter.ai/api/v1"
            
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://azucar.aeisoftware.com",
        "X-Title": "Azucar Control"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hola"}
        ],
        "max_tokens": 10
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                res_data = response.json()
                try:
                    content = res_data["choices"][0]["message"]["content"]
                    return {"success": True, "message": "Conexión exitosa", "response": content}
                except (KeyError, IndexError) as parse_err:
                    return {
                        "success": False,
                        "message": "Respuesta en formato inesperado",
                        "details": f"Error parseando: {parse_err}. Respuesta: {res_data}"
                    }
            else:
                try:
                    error_detail = response.json()
                except Exception:
                    error_detail = response.text
                return {
                    "success": False,
                    "message": f"Error del proveedor (HTTP {response.status_code})",
                    "details": error_detail
                }
    except Exception as ex:
        return {
            "success": False,
            "message": "Error al conectar con el servidor",
            "details": str(ex)
        }

