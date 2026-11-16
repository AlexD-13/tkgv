from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from schemas.registration import RegistrationCreate, RegistrationRead
from services.registration_service import (
    count_by_dish,
    create_registration,
    list_by_client,
)

router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.get("", response_model=list[RegistrationRead])
async def get_registrations(
    client_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
):
    if not client_id:
        return []
    return await list_by_client(db, client_id)


@router.post("", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
async def post_registration(
    payload: RegistrationCreate, db: AsyncSession = Depends(get_session)
):
    try:
        return await create_registration(db, payload)
    except ValueError as exc:
        message = str(exc)
        if "full" in message:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
