import random
import string
import redis
from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os
import jwt
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from authlib.integrations.starlette_client import OAuthError

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "https://gpt-2ait.vercel.app",
                   "https://gpt-seven-sand.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    session_cookie="session_cookie",
    same_site="none",  # Required for cross-origin cookies
    https_only=True,  # Required for secure cookies
    max_age=3600  # 1 hour
)

# OAuth
oauth = OAuth()
# Update your OAuth setup (add GitHub registration)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Add GitHub OAuth registration
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# Redis setup
redis_host = "localhost"
redis_port = 6379
r = redis.Redis(
        host='redis-14245.c321.us-east-1-2.ec2.redns.redis-cloud.com',
    port=14245,
    decode_responses=True,
    username="default",
    password="UL5tpo8dma2OCBbi88QxICIfyeoxDQcd",
)

# Rate Limit Config
MAX_TOKENS = 100  # Max number of tokens
REFILL_RATE = 1  # 1 token per second
USER_ID = "user_1"
TOKEN_COST_PER_REQUEST = 5  # Each request will cost 5 tokens
DELAY_AFTER_EXCEED = 30  # Delay after rate limit is exceeded in seconds

def get_tokens(user_id: str):
    return int(r.get(f"tokens:{user_id}") or MAX_TOKENS)

def refill_tokens(user_id: str):
    now = int(time.time())
    last = int(r.get(f"last_refill:{user_id}") or now)
    tokens = get_tokens(user_id)

    if now > last:
        elapsed = now - last
        tokens = min(tokens + elapsed * REFILL_RATE, MAX_TOKENS)
        r.set(f"tokens:{user_id}", tokens)
        r.set(f"last_refill:{user_id}", now)

    return tokens

def token_bucket_rate_limit(user_id: str):
    tokens = refill_tokens(user_id)
    if tokens <= 0:
        # Apply delay if rate limit is exceeded
        last_refill_time = int(r.get(f"last_refill:{user_id}"))
        reset_time = last_refill_time + DELAY_AFTER_EXCEED
        time_left = reset_time - int(time.time())
        
        if time_left > 0:
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Please try again after {time_left} seconds.")
    r.decr(f"tokens:{user_id}", TOKEN_COST_PER_REQUEST)  # Deduct tokens per request

@app.get("/rate-limit-status")
async def rate_limit_status():
    user_id = USER_ID
    tokens = refill_tokens(user_id)
    if tokens <= 0:
        last_refill_time = int(r.get(f"last_refill:{user_id}"))
        reset_time = last_refill_time + DELAY_AFTER_EXCEED
        time_left = reset_time - int(time.time())
        return {
            "status": "exceeded",
            "message": f"❌ Rate limit exceeded. Please try again after {time_left} seconds.",
            "tokens": 0
        }
    return {
        "status": "available",
        "message": f"✅ You have {tokens} tokens left.",
        "tokens": tokens
    }

@app.get("/")
async def root():
    return {"message": "Welcome to Unsungfields AI"}

@app.get("/login/google")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    try:
        user = await oauth.google.parse_id_token(request, token)
    except Exception:
        user = None
    if not user:
        resp = await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo", token=token)
        user = resp.json()
    frontend_url = "http://localhost:5173/success"
    params = urlencode({
        "name": user.get("name"),
        "email": user.get("email"),
        "picture": user.get("picture")
    })
    return RedirectResponse(f"{frontend_url}?{params}")

@app.post("/request-magic-link")
async def request_magic_link(payload: dict = Body(...)):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Set expiry to 1 hour
    expiry = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode(
        {"email": email, "exp": expiry},
        os.getenv("JWT_SECRET_KEY"),
        algorithm="HS256"
    )
    magic_link = f"http://localhost:5173/verify?token={token}"

    # Send email
    try:
        send_magic_link_email(email, magic_link)
        return {"message": "Magic link has been sent to your email."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

def send_magic_link_email(to_email: str, magic_link: str):
    # Email configuration (using Gmail SMTP)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("SMTP_EMAIL")  # Your Gmail
    sender_password = os.getenv("SMTP_PASSWORD")  # App password (not regular password)

    # Create message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Your Magic Login Link"

    # Email body (HTML)
    html = f"""
    <html>
      <body>
        <h2>Unsungfields AI Login</h2>
        <p>Click the link below to log in (expires in 1 hour):</p>
        <a href="{magic_link}" style="
          display: inline-block;
          padding: 10px 20px;
          background-color: #4CAF50;
          color: white;
          text-decoration: none;
          border-radius: 5px;
        ">Login Now</a>
        <p>Or copy this link:</p>
        <p>{magic_link}</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    # Send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

@app.get("/verify-magic-link")
async def verify_magic_link(token: str):
    try:
        decoded = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        return {"email": decoded.get("email")}
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

# API Key Management
def generate_api_key():
    return f"UFK_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"

@app.post("/api/keys")
async def create_api_key(payload: dict = Body(...)):
    display_name = payload.get("display_name")
    if not display_name:
        raise HTTPException(status_code=400, detail="Display name is required")
    api_key = generate_api_key()
    r.setex(f"api_key:{USER_ID}:{api_key}", timedelta(days=30), display_name)
    return {"message": "API Key created successfully", "api_key": api_key}

@app.get("/api/keys")
async def list_api_keys():
    keys = []
    for key in r.scan_iter(f"api_key:{USER_ID}:*"):
        display_name = r.get(key)
        keys.append({
            "display_name": display_name,
            "key": key.split(":")[-1][:3]
        })
    return {"api_keys": keys}

@app.delete("/api/keys/{api_key}")
async def delete_api_key(api_key: str):
    # Construct the exact key to delete
    exact_key = f"api_key:{USER_ID}:{api_key}"
    
    # Verify the exact key exists
    if not r.exists(exact_key):
        raise HTTPException(status_code=404, detail="API Key not found")
    
    # Delete only the exact key
    r.delete(exact_key)
    return {"message": f"API Key {api_key[:3]}... deleted successfully"}

# Add GitHub login route
@app.get("/login/github")
async def login_github(request: Request):
    redirect_uri = request.url_for("auth_github")
    return await oauth.github.authorize_redirect(request, redirect_uri)

# Add GitHub auth callback route
@app.get("/auth/github")
async def auth_github(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get user info from GitHub
    try:
        resp = await oauth.github.get('user', token=token)
        user_data = resp.json()
        
        # For email (GitHub requires separate request for primary email)
        email_resp = await oauth.github.get('user/emails', token=token)
        emails = email_resp.json()
        primary_email = next((e['email'] for e in emails if e['primary']), None)
        
        if not primary_email:
            raise HTTPException(status_code=400, detail="No primary email found")
        
        frontend_url = "http://localhost:5173/success"
        params = urlencode({
            "name": user_data.get("name") or user_data.get("login"),
            "email": primary_email,
            "picture": user_data.get("avatar_url")
        })
        return RedirectResponse(f"{frontend_url}?{params}")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch user info: {str(e)}")