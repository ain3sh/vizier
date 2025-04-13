from fastapi import APIRouter, Request, Depends, HTTPException
from database import database
from jose import jwt
from uuid import UUID
import os

router = APIRouter(prefix="/user", tags=["user"])

JWT_SECRET = os.getenv("JWT_SECRET")

def get_current_user(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return UUID(payload["sub"])
    except Exception as e:
        print("❌ Invalid token:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me")
async def get_user_profile(request: Request):
    user_id = get_current_user(request)

    user = await database.fetch_one("""
        SELECT name, email, archetype, user_experience
        FROM users WHERE user_id = :user_id
    """, {"user_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": user["name"],
        "email": user["email"],
        "archetype": user["archetype"],
        "user_experience": user["user_experience"]
    }

@router.post("/profile")
async def update_user_profile(data: dict, request: Request):
    user_id = get_current_user(request)

    update_query = """
    UPDATE users
    SET archetype = :archetype,
        user_description = :user_description,
        user_goals = :user_goals,
        user_experience = :user_experience
    WHERE user_id = :user_id
    """

    await database.execute(update_query, {
        "archetype": data.get("archetype"),
        "user_description": data.get("user_description"),
        "user_goals": data.get("user_goals"),
        "user_experience": data.get("user_experience"),
        "user_id": user_id
    })

    return {"message": "Profile updated", "data": data}
