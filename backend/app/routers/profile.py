from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.profile import UserProfile
from app.schemas.profile import ProfileUpsert, ProfileOut
from app.services.macro_engine import calculate_targets

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("", response_model=ProfileOut)
def getprofile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not set up yet")
    return profile

@router.put("", response_model=ProfileOut)
def upsert_profile(
    payload: ProfileUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    targets = calculate_targets(
        weight_kg = payload.weight_kg,
        height_cm = payload.height_cm,
        age = payload.age,
        sex = payload.sex,
        activity_level = payload.activity_level,
        goal = payload.goal
    )

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if profile: 
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
        for key, value in targets.items():
            setattr(profile, key, value)
    else: 
        profile = UserProfile(user_id=current_user.id, **payload.model_dump(), **targets)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile
