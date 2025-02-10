from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, EmailStr, constr, Field
from typing import List, Dict, Optional, Annotated
from datetime import datetime, timedelta, UTC
from jose import jwt
import praw
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.fernet import Fernet
import secrets

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middlewares
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "your-domain.com"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configurations
SECRET_KEY = secrets.token_urlsafe(32)  # Generate secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# MongoDB connection
MONGODB_URL = "mongodb://localhost:27017"  # Store this in environment variables
client = AsyncIOMotorClient(MONGODB_URL)
db = client.saveddit

# Models
class UserCreate(BaseModel):
    email: EmailStr
    username: Annotated[str, Field(min_length=3, max_length=50)]
    password: Annotated[str, Field(min_length=8, pattern=r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$")]

class User(BaseModel):
    email: EmailStr
    username: str
    reddit_credentials_stored: bool = False

class RedditCredentials(BaseModel):
    username: str
    password: str

class AppConfig:
    REDDIT_CLIENT_ID = "your_client_id"  # Store in env
    REDDIT_CLIENT_SECRET = "your_client_secret"  # Store in env
    USER_AGENT = "SavedPostsFetcher/1.0"

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

# Helper function to encrypt Reddit credentials
def encrypt_credentials(credentials: dict) -> dict:
    return {
        key: fernet.encrypt(value.encode()).decode()
        for key, value in credentials.items()
    }

def decrypt_credentials(credentials: dict) -> dict:
    return {
        key: fernet.decrypt(value.encode()).decode()
        for key, value in credentials.items()
    }

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Rate limit decorators for endpoints
@app.post("/auth/register", response_model=User)
@limiter.limit("5/minute")
async def register_user(request: Request, user: UserCreate):
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = {
        "email": user.email,
        "username": user.username,
        "password": get_password_hash(user.password),
        "reddit_credentials_stored": False
    }
    
    await db.users.insert_one(user_dict)
    return User(**user_dict)

@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/reddit/credentials")
@limiter.limit("10/minute")
async def store_reddit_credentials(
    request: Request,
    credentials: RedditCredentials,
    current_user: User = Depends(get_current_user)
):
    # Verify Reddit credentials before storing
    try:
        reddit = praw.Reddit(
            client_id=AppConfig.REDDIT_CLIENT_ID,
            client_secret=AppConfig.REDDIT_CLIENT_SECRET,
            user_agent=AppConfig.USER_AGENT,
            username=credentials.username,
            password=credentials.password
        )
        # Verify credentials work
        reddit.user.me()
        
        # Encrypt and store credentials
        encrypted_creds = encrypt_credentials({
            "username": credentials.username,
            "password": credentials.password
        })
        
        await db.users.update_one(
            {"email": current_user.email},
            {
                "$set": {
                    "reddit_credentials": encrypted_creds,
                    "reddit_credentials_stored": True
                }
            }
        )
        return {"message": "Reddit credentials stored successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Reddit credentials"
        )

@app.get("/reddit/saved", response_model=List[Dict])
async def get_saved_items(current_user: User = Depends(get_current_user)):
    user = await db.users.find_one({"email": current_user.email})
    
    if not user.get("reddit_credentials_stored"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reddit credentials not stored"
        )
    
    try:
        # Decrypt credentials
        decrypted_creds = decrypt_credentials(user["reddit_credentials"])
        
        reddit = praw.Reddit(
            client_id=AppConfig.REDDIT_CLIENT_ID,
            client_secret=AppConfig.REDDIT_CLIENT_SECRET,
            user_agent=AppConfig.USER_AGENT,
            username=decrypted_creds["username"],
            password=decrypted_creds["password"]
        )

        saved_items = []
        for item in reddit.user.me().saved(limit=None):
            saved_item = {
                "type": "comment" if isinstance(item, praw.models.Comment) else "post",
                "title": item.body if isinstance(item, praw.models.Comment) else item.title,
                "url": f"https://reddit.com{item.permalink}",
                "subreddit": item.subreddit.display_name
            }
            saved_items.append(saved_item)
        
        return saved_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )