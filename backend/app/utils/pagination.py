"""
Pagination utilities for API endpoints
"""
from typing import TypeVar, List, Dict, Any, Tuple
from sqlalchemy import select, func
from sqlalchemy.sql import Select
from sqlalchemy.ext.asyncio import AsyncSession

# Import and re-export PaginationParams
from app.schemas.common import PaginationParams

__all__ = ["paginate", "PaginationParams"]

T = TypeVar('T')

async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Apply pagination to a SQLAlchemy query and return results with pagination metadata
    
    Args:
        db: AsyncSession - Database session
        query: Select - SQLAlchemy select query
        params: PaginationParams - Pagination parameters (page, limit)
        
    Returns:
        Tuple containing:
        - List of query results
        - Dictionary with pagination metadata (page, limit, total, pages)
    """
    # Count total items
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    paginated_query = query.offset((params.page - 1) * params.limit).limit(params.limit)
    
    # Execute query
    result = await db.execute(paginated_query)
    items = result.scalars().all()
    
    # Calculate pagination metadata
    pages = (total + params.limit - 1) // params.limit if total > 0 else 0
    
    # Create pagination metadata
    pagination = {
        "page": params.page,
        "limit": params.limit,
        "total": total,
        "pages": pages
    }
    
    return items, pagination