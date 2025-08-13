from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.upload import Upload, ProcessingStatus
from app.schemas.upload import UploadStatistics, Upload as UploadSchema
from app.utils.dependencies import get_current_user, get_admin_user


router = APIRouter()


@router.get("/statistics", response_model=UploadStatistics)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get upload statistics for the current user
    """
    # Count total uploads
    total_uploads = db.query(Upload).filter(Upload.user_id == current_user.id).count()
    
    # Count completed uploads
    completed = db.query(Upload).filter(
        Upload.user_id == current_user.id,
        Upload.status == ProcessingStatus.COMPLETED
    ).count()
    
    # Count in-progress uploads
    in_progress = db.query(Upload).filter(
        Upload.user_id == current_user.id,
        Upload.status.in_([ProcessingStatus.PENDING, ProcessingStatus.PROCESSING])
    ).count()
    
    # Count failed uploads
    failed = db.query(Upload).filter(
        Upload.user_id == current_user.id,
        Upload.status == ProcessingStatus.FAILED
    ).count()
    
    return {
        "total_uploads": total_uploads,
        "completed": completed,
        "in_progress": in_progress,
        "failed": failed
    }


@router.get("/admin", response_model=List[UploadSchema])
def get_admin_dashboard(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Ensure admin access
) -> Any:
    """
    Admin dashboard: Get all uploads with filtering options
    """
    query = db.query(Upload)
    
    # Apply filters
    if status:
        try:
            query = query.filter(Upload.status == ProcessingStatus(status))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    if user_id:
        query = query.filter(Upload.user_id == user_id)
    
    if start_date:
        query = query.filter(Upload.created_at >= start_date)
    
    if end_date:
        query = query.filter(Upload.created_at <= end_date)
    
    # Execute query with pagination
    uploads = (
        query
        .order_by(Upload.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return uploads


@router.get("/admin/statistics", response_model=Dict[str, Any])
def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Ensure admin access
) -> Any:
    """
    Admin dashboard: Get overall system statistics
    """
    # Count total uploads
    total_uploads = db.query(Upload).count()
    
    # Count users
    total_users = db.query(User).count()
    premium_users = db.query(User).filter(User.role == UserRole.PREMIUM).count()
    free_users = db.query(User).filter(User.role == UserRole.FREE).count()
    
    # Count uploads by status
    completed = db.query(Upload).filter(Upload.status == ProcessingStatus.COMPLETED).count()
    pending = db.query(Upload).filter(Upload.status == ProcessingStatus.PENDING).count()
    processing = db.query(Upload).filter(Upload.status == ProcessingStatus.PROCESSING).count()
    failed = db.query(Upload).filter(Upload.status == ProcessingStatus.FAILED).count()
    
    # Get today's uploads
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    today_uploads = db.query(Upload).filter(
        Upload.created_at >= today,
        Upload.created_at < tomorrow
    ).count()
    
    # Calculate average processing time for completed uploads
    avg_processing_time_query = db.query(
        func.avg(Upload.processing_time)
    ).filter(
        Upload.status == ProcessingStatus.COMPLETED,
        Upload.processing_time != None
    ).scalar()
    
    avg_processing_time = float(avg_processing_time_query) if avg_processing_time_query else 0
    
    return {
        "total_uploads": total_uploads,
        "total_users": total_users,
        "premium_users": premium_users,
        "free_users": free_users,
        "completed": completed,
        "pending": pending,
        "processing": processing,
        "failed": failed,
        "today_uploads": today_uploads,
        "avg_processing_time": avg_processing_time
    }