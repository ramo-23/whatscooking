# app/routers/pantry.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.pantry import PantryItem
from app.schemas.pantry import PantryItemCreate, PantryItemUpdate, PantryItemOut
from app.utils.normalize import normalize_ingredient_name

router = APIRouter(prefix="/pantry", tags=["pantry"])

@router.get("", response_model=list[PantryItemOut])
def get_pantry_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(PantryItem).filter(PantryItem.user_id == current_user.id).all()
    return items

@router.post("", response_model=PantryItemOut, status_code=status.HTTP_201_CREATED)
def create_pantry_item(
    payload: PantryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Normalize name before saving
    normalized_name = normalize_ingredient_name(payload.ingredient_name)
    
    item = PantryItem(
        user_id=current_user.id,
        ingredient_name=normalized_name,
        quantity=payload.quantity,
        unit=payload.unit,
        expiry_date=payload.expiry_date
    )
    
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.patch("/{item_id}", response_model=PantryItemOut)
def update_pantry_item(
    item_id: uuid.UUID,
    payload: PantryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(PantryItem).filter(PantryItem.id == item_id).first()
    
    # Unified 404 response for both "doesn't exist" and "not yours"
    if not item or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found"
        )
        
    update_data = payload.model_dump(exclude_unset=True)
    
    if "ingredient_name" in update_data:
        update_data["ingredient_name"] = normalize_ingredient_name(update_data["ingredient_name"])
        
    for key, value in update_data.items():
        setattr(item, key, value)
        
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pantry_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(PantryItem).filter(PantryItem.id == item_id).first()
    
    if not item or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found"
        )
        
    db.delete(item)
    db.commit()
    return None