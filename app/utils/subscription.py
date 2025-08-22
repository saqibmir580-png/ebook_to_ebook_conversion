from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionStatus
from app.services.subscription import SubscriptionService
from app.db.session import get_db
from app.core.auth import get_current_active_user

def check_subscription():
    """
    Dependency to check if the current user has an active subscription.
    Raises 403 if the subscription is not active or has expired.
    """
    async def _check_subscription(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.subscription_status != SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your subscription is not active. Please upgrade to continue.",
            )
        
        # Additional checks can be added here (e.g., subscription expiry)
        return current_user
    
    return _check_subscription

def check_export_permission(format: str):
    """
    Dependency to check if the user's subscription allows exporting to the specified format.
    """
    async def _check_export_permission(
        current_user: User = Depends(get_current_active_user)
    ) -> bool:
        if not SubscriptionService.can_export_format(current_user, format):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your current plan does not support {format.upper()} exports. Please upgrade to a premium plan."
            )
        return True
    
    return _check_export_permission

def check_usage_limit(resource_type: str, amount: int = 1):
    """
    Dependency to check if the user has enough quota for a specific resource.
    """
    async def _check_usage_limit(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> bool:
        if SubscriptionService.check_usage_limit(current_user, resource_type, amount):
            limit = current_user.plan_limits.get(resource_type)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"You have reached your {resource_type.replace('_', ' ')} limit.",
                    "code": f"{resource_type}_limit_reached",
                    "limit": limit
                }
            )
        return True
    
    return _check_usage_limit
