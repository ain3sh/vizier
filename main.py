from fastapi import FastAPI
from routers import auth

app = FastAPI()
app.include_router(auth.router)

@app.on_event("startup")
async def startup():
    pass  # skip DB connect for now

@app.on_event("shutdown")
async def shutdown():
    pass