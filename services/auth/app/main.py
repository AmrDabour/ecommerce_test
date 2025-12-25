"""
Authentication Service - Main Application
Handles user authentication, registration, and JWT token management
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import uvicorn

from config import get_settings
from database import engine, get_db
from models import Base, User, RefreshToken, Address
from schemas import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    Token, RefreshTokenRequest, MessageResponse,
    AddressCreate, AddressResponse, AddressUpdate,
    PasswordChange
)
from security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, verify_token_type
)
from dependencies import get_current_user, get_current_active_user, require_admin

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="E-Commerce Authentication Service",
    description="Microservice for user authentication and authorization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# ==========================================
# STARTUP & HEALTH CHECK
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ {settings.SERVICE_NAME} started successfully")
    print(f"📊 Database: {settings.DB_NAME}")
    print(f"🔐 JWT Expiry: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")


@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": settings.SERVICE_NAME,
            "database": "connected",
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        avatar_url=user_data.avatar_url,
        role="user",  # Default role
        is_verified=False,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get access token
    """
    # Find user
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Create tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store refresh token in database
    expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )
    db.add(db_refresh_token)

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.post("/auth/refresh", response_model=Token)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Decode refresh token
    payload = decode_token(refresh_data.refresh_token)
    if payload is None or not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if token exists in database and is not revoked
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_data.refresh_token,
        RefreshToken.is_revoked == False
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked"
        )

    # Check if token is expired
    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    # Get user
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Revoke old refresh token and store new one
    db_token.is_revoked = True
    new_db_token = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_db_token)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@app.post("/auth/logout", response_model=MessageResponse)
async def logout(
    refresh_data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout and revoke refresh token
    """
    # Revoke refresh token
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_data.refresh_token,
        RefreshToken.user_id == current_user.id
    ).first()

    if db_token:
        db_token.is_revoked = True
        db.commit()

    return {"message": "Logged out successfully"}


# ==========================================
# USER PROFILE ENDPOINTS
# ==========================================

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile
    """
    return current_user


@app.put("/users/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    """
    # Update fields
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@app.post("/users/me/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password changed successfully"}


# ==========================================
# ADDRESS ENDPOINTS
# ==========================================

@app.get("/users/me/addresses", response_model=list[AddressResponse])
async def get_user_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all addresses for current user
    """
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return addresses


@app.post("/users/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new address for current user
    """
    # If this is set as default, unset other default addresses of the same type
    if address_data.is_default:
        db.query(Address).filter(
            Address.user_id == current_user.id,
            Address.type == address_data.type
        ).update({"is_default": False})

    new_address = Address(
        user_id=current_user.id,
        **address_data.model_dump()
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address


@app.put("/users/me/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: int,
    address_update: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update address
    """
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    # Update fields
    update_data = address_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(address, key, value)

    # If setting as default, unset other defaults
    if address_update.is_default:
        db.query(Address).filter(
            Address.user_id == current_user.id,
            Address.type == address.type,
            Address.id != address_id
        ).update({"is_default": False})

    address.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(address)

    return address


@app.delete("/users/me/addresses/{address_id}", response_model=MessageResponse)
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete address
    """
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    db.delete(address)
    db.commit()

    return {"message": "Address deleted successfully"}


# ==========================================
# ADMIN ENDPOINTS
# ==========================================

@app.get("/admin/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@app.get("/admin/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


# ==========================================
# TOKEN VERIFICATION ENDPOINT (for other services)
# ==========================================

@app.get("/auth/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify token and return user info (for inter-service communication)
    """
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified
    }


if __name__ == "__main__":
    print(f"🚀 Starting {settings.SERVICE_NAME}...")
    print(f"📍 Port: {settings.SERVICE_PORT}")
    print(f"📚 Docs: http://localhost:{settings.SERVICE_PORT}/docs")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        log_level="info"
    )
