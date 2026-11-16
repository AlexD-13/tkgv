from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from schemas.dish import DishPublic
from services.dish_service import list_public

router = APIRouter(prefix="/dishes", tags=["dishes"])


@router.get("", response_model=list[DishPublic])
async def get_dishes(db: AsyncSession = Depends(get_session)):
    return await list_public(db)
