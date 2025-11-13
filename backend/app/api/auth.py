from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import UserRegister, UserLogin, Token, User
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token
from app.core.database import get_database
from bson import ObjectId
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db=Depends(get_database)):
    try:
        print(f"Registration attempt for email: {user_data.email}")
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            print(f"User already exists: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        from datetime import datetime
        user_dict = {
            "name": user_data.name,
            "email": user_data.email,
            "password": hashed_password,
            "created_at": datetime.utcnow()
        }
        
        result = await db.users.insert_one(user_dict)
        print(f"User created successfully: {result.inserted_id}")
        
        return {
            "user_id": str(result.inserted_id),
            "email": user_data.email,
            "message": "User registered successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db=Depends(get_database)):
    try:
        print(f"Login attempt for email: {user_credentials.email}")
        
        # Find user by email
        user = await db.users.find_one({"email": user_credentials.email})
        if not user:
            print(f"User not found: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(user_credentials.password, user["password"]):
            print(f"Invalid password for user: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": str(user["_id"])},
            expires_delta=access_token_expires
        )
        
        print(f"Login successful for user: {user_credentials.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30 minutes in seconds
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=dict)
async def get_current_user(current_user: dict = Depends(verify_token), db=Depends(get_database)):
    try:
        user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )