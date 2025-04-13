from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from jose import jwt
from httpx import AsyncClient
import os
import uuid
from uuid import UUID
from dotenv import load_dotenv
from database import database

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET")




'''url for frontend/testing to use: https://accounts.google.com/o/oauth2/v2/auth?
response_type=code&
client_id=YOUR_GOOGLE_CLIENT_ID&
redirect_uri=http://localhost:8000/auth/callback&
scope=email%20profile&
access_type=offline&
prompt=consent'''

@router.get("/callback")
async def google_auth_callback(code: str):
    print("🔐 Step 1: Received code from Google:", code)

    # exchange code for tokens
    async with AsyncClient() as client:
        print("🌐 Step 2: Exchanging code for access token...")
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        })
        token_data = token_res.json()
        access_token = token_data.get("access_token")

        print("🔑 Access token received:", access_token)

        if not access_token:
            print("❌ Failed to get access token:", token_data)
            raise HTTPException(status_code=401, detail="Invalid code/token exchange")

        # get user info
        print("👤 Step 3: Fetching user info from Google...")
        userinfo_res = await client.get("https://www.googleapis.com/oauth2/v2/userinfo",
                                        headers={"Authorization": f"Bearer {access_token}"})
        userinfo = userinfo_res.json()
        print("✅ User info received:", userinfo)

        email = userinfo["email"]
        google_id = userinfo["id"]
        name = userinfo.get("name", "")
        picture = userinfo.get("picture", "")

    # Step 4: Check DB for user
    query = "SELECT * FROM users WHERE email = :email"
    user = await database.fetch_one(query, {"email": email})

    if not user:
        print("➕ Creating new user in DB")
        user_id = str(uuid.uuid4())
        insert_query = """
        INSERT INTO users (
            user_id, email, name, google_id, picture_url,
            archetype, user_description, user_goals, user_experience, acct_created_date
        ) VALUES (
            :user_id, :email, :name, :google_id, :picture,
            NULL, NULL, NULL, NULL, NOW()
        )
        """
        await database.execute(insert_query, {
            "user_id": user_id,
            "email": email,
            "name": name,
            "google_id": google_id,
            "picture": picture
        })
    else:
        print("✅ User found in DB")
        user_id = user["user_id"]

    print("🔐 Step 5: Issuing JWT for user:", user_id)
    token = jwt.encode({"sub": str(user_id)}, JWT_SECRET, algorithm="HS256")

    print("🎉 Step 6: Returning JWT to client")
    #return {"access_token": token}
    print(token)
    return RedirectResponse(f"http://localhost:5173/login/success?token={token}")
    #change this to redirect response    


@router.get("/me")
async def get_me(request: Request):
    auth_header = request.headers.get("authorization")
    print("🔐 Raw Authorization header:", auth_header)

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"user_id": UUID(payload["sub"])}
    except Exception as e:
        print("❌ Invalid token:", e)
        raise HTTPException(status_code=401, detail="Invalid token")
