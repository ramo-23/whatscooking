from datetime import datetime, date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import MealLog, Recipe, UserProfile
from app.deps import get_current_user
from app.schemas.meal_log import MealLogCreate, MealLogOut, DailySummary
from app.models.user import User

router = APIRouter(prefix="/meal-log", tags=["meal-log"])


@router.post("", response_model=MealLogOut, status_code=status.HTTP_201_CREATED)
def log_meal(
    meal_data: MealLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log a meal for today."""
    
    if meal_data.recipe_id:
        # Recipe doesn't have user_id - it's shared/public
        recipe = db.query(Recipe).filter(
            Recipe.id == meal_data.recipe_id
        ).first()
        
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        meal_log = MealLog(
            user_id=current_user.id,
            recipe_id=recipe.id,
            meal_name=recipe.title,
            logged_at=datetime.utcnow(),
            calories=recipe.calories,
            protein_g=recipe.protein_g,
            carbs_g=recipe.carbs_g,
            fat_g=recipe.fat_g,
        )
    else:
        # Manual entry - must provide macros
        if None in [meal_data.calories, meal_data.protein_g, 
                    meal_data.carbs_g, meal_data.fat_g]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manual entries require calories, protein_g, carbs_g, and fat_g"
            )
        
        if not meal_data.meal_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manual entries require a meal_name"
            )
        
        meal_log = MealLog(
            user_id=current_user.id,
            recipe_id=None,
            meal_name=meal_data.meal_name,
            logged_at=datetime.utcnow(),
            calories=meal_data.calories,
            protein_g=meal_data.protein_g,
            carbs_g=meal_data.carbs_g,
            fat_g=meal_data.fat_g,
        )
    
    db.add(meal_log)
    db.commit()
    db.refresh(meal_log)
    return meal_log


@router.get("/today", response_model=DailySummary)
def get_today_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get today's logged meals with running totals vs targets."""
    
    today = date.today()
    start_of_day = datetime(today.year, today.month, today.day)
    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)
    
    meals = db.query(MealLog).filter(
        MealLog.user_id == current_user.id,
        MealLog.logged_at >= start_of_day,
        MealLog.logged_at <= end_of_day
    ).order_by(MealLog.logged_at.desc()).all()
    
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found - please set your goals first"
        )
    
    total_calories = sum(int(meal.calories or 0) for meal in meals)
    total_protein_g = sum(float(meal.protein_g or 0.0) for meal in meals)
    total_carbs_g = sum(float(meal.carbs_g or 0.0) for meal in meals)
    total_fat_g = sum(float(meal.fat_g or 0.0) for meal in meals)
    
    # Convert Numeric columns to Python types
    target_calories = int(profile.target_calories or 0)
    target_protein_g = float(profile.target_protein_g or 0.0)
    target_carbs_g = float(profile.target_carbs_g or 0.0)
    target_fat_g = float(profile.target_fat_g or 0.0)
    
    remaining_calories = max(0, target_calories - total_calories)
    remaining_protein_g = max(0.0, target_protein_g - total_protein_g)
    remaining_carbs_g = max(0.0, target_carbs_g - total_carbs_g)
    remaining_fat_g = max(0.0, target_fat_g - total_fat_g)
    
    meals_with_names = [MealLogOut.model_validate(meal) for meal in meals]
    
    return DailySummary(
        date=today.isoformat(),
        total_calories=total_calories,
        total_protein_g=total_protein_g,
        total_carbs_g=total_carbs_g,
        total_fat_g=total_fat_g,
        target_calories=target_calories,
        target_protein_g=target_protein_g,
        target_carbs_g=target_carbs_g,
        target_fat_g=target_fat_g,
        remaining_calories=remaining_calories,
        remaining_protein_g=remaining_protein_g,
        remaining_carbs_g=remaining_carbs_g,
        remaining_fat_g=remaining_fat_g,
        meals=meals_with_names
    )


@router.delete("/{meal_log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_log(
    meal_log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a meal log entry (ownership-checked)."""
    
    meal_log = db.query(MealLog).filter(
        MealLog.id == meal_log_id,
        MealLog.user_id == current_user.id
    ).first()
    
    if not meal_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal log not found or doesn't belong to you"
        )
    
    db.delete(meal_log)
    db.commit()