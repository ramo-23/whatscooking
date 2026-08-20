from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, pantry, recipes, profile, meal_log, suggestions

app = FastAPI(title="WhatsCooking API")
app.include_router(auth.router)
app.include_router(pantry.router)
app.include_router(recipes.router)
app.include_router(profile.router)
app.include_router(meal_log.router)
app.include_router(suggestions.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}