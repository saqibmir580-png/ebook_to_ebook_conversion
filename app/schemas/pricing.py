from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class PricingPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: float
    max_file_size: int
    daily_conversions_limit: int
    is_active: bool = True


class PricingPlanCreate(PricingPlanBase):
    pass


class PricingPlanUpdate(PricingPlanBase):
    pass


class PricingPlanInDBBase(PricingPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PricingPlan(PricingPlanInDBBase):
    pass