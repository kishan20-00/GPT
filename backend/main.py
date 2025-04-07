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
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "supersecret"))

# OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Redis setup
redis_host = "localhost"
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)

# Rate Limit Config
MAX_TOKENS = 100  # Max number of tokens
REFILL_RATE = 1  # 1 token per second
USER_ID = "user_1"
TOKEN_COST_PER_REQUEST = 5  # Each request to generate will cost 5 tokens
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

# Rate Limit Status Endpoint
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

@app.get("/login")
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
        return {"error": "Email is required"}
    expiry = datetime.utcnow() + timedelta(minutes=int(os.getenv("JWT_EXPIRY_MINUTES", 15)))
    token = jwt.encode({"email": email, "exp": expiry}, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
    magic_link = f"http://localhost:5173/verify?token={token}"
    print(f"\n🔗 Magic login link for {email}:\n{magic_link}\n")
    return {"message": "Magic link has been generated. (See server console)"}

@app.get("/verify-magic-link")
async def verify_magic_link(token: str):
    try:
        decoded = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        return {"email": decoded.get("email")}
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

# Model
model_path = "C:/Users/HP/Desktop/Unsungfields-AI/backend/tiny-gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

@app.post("/generate")
async def generate(data: dict = Body(...)):
    token_bucket_rate_limit(USER_ID)  # 🛡️ Rate limit check
    prompt = data.get("prompt", "")
    temperature = float(data.get("temperature", 0.7))
    max_tokens = int(data.get("max_tokens", 100))
    start = time.time()
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    output = model.generate(
        input_ids,
        max_new_tokens=max_tokens,
        temperature=temperature,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    end = time.time()
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return {
        "response": generated_text,
        "latency": round((end - start) * 1000, 2),
        "tokens_per_second": round(len(output[0]) / (end - start), 2)
    }

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
    key = f"api_key:{USER_ID}:{api_key}"
    if not r.exists(key):
        raise HTTPException(status_code=404, detail="API Key not found")
    r.delete(key)
    return {"message": f"API Key {api_key} deleted successfully"}
