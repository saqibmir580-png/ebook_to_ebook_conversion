from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pricing import PricingPlan
from app.schemas.pricing import (
    PricingPlan as PricingPlanSchema,
    PricingPlanCreate,
    PricingPlanUpdate
)
from app.utils.dependencies import get_current_user, get_admin_user


router = APIRouter()


@router.get("", response_model=List[PricingPlanSchema])
def get_pricing_plans(
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all active pricing plans
    """
    plans = db.query(PricingPlan).filter(PricingPlan.is_active == True).all()
    return plans


@router.post("", response_model=PricingPlanSchema)
def create_pricing_plan(
    *,
    db: Session = Depends(get_db),
    plan_in: PricingPlanCreate,
    current_user: Any = Depends(get_admin_user)  # Ensure admin access
) -> Any:
    """
    Create a new pricing plan (admin only)
    """
    # Check if plan with the same name already exists
    existing_plan = db.query(PricingPlan).filter(PricingPlan.name == plan_in.name).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pricing plan with this name already exists"
        )
    
    # Create new plan
    plan = PricingPlan(
        name=plan_in.name,
        description=plan_in.description,
        price_monthly=plan_in.price_monthly,
        price_yearly=plan_in.price_yearly,
        max_file_size=plan_in.max_file_size,
        daily_conversions_limit=plan_in.daily_conversions_limit,
        is_active=plan_in.is_active
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return plan


@router.put("/{plan_id}", response_model=PricingPlanSchema)
def update_pricing_plan(
    *,
    db: Session = Depends(get_db),
    plan_id: int,
    plan_in: PricingPlanUpdate,
    current_user: Any = Depends(get_admin_user)  # Ensure admin access
) -> Any:
    """
    Update a pricing plan (admin only)
    """
    plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing plan not found"
        )
    
    # Check if plan with the same name already exists (if name is being updated)
    if plan_in.name != plan.name:
        existing_plan = db.query(PricingPlan).filter(PricingPlan.name == plan_in.name).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pricing plan with this name already exists"
            )
    
    # Update plan attributes
    for field in plan_in.__dict__:
        if field != "id" and hasattr(plan, field):
            setattr(plan, field, getattr(plan_in, field))
    
    db.commit()
    db.refresh(plan)
    
    return plan


@router.delete("/{plan_id}")
def delete_pricing_plan(
    *,
    db: Session = Depends(get_db),
    plan_id: int,
    current_user: Any = Depends(get_admin_user)  # Ensure admin access
) -> Any:
    """
    Delete a pricing plan (admin only)
    """
    plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing plan not found"
        )
    
    db.delete(plan)
    db.commit()
    
    return {"message": "Pricing plan deleted successfully"}