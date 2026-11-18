from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from schemas.registration import RegistrationCreate, RegistrationRead
from services.registration_service import (
    claim_registration,
    count_by_dish,
    create_registration,
    delete_owned_registration,
    list_by_client,
    search_by_name,
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


@router.get("/search", response_model=list[RegistrationRead])
async def search_registrations(
    q: str = Query(min_length=2),
    db: AsyncSession = Depends(get_session),
):
    return await search_by_name(db, q)


@router.delete("/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_registration(
    registration_id: int,
    client_id: str = Query(...),
    db: AsyncSession = Depends(get_session),
):
    ok = await delete_owned_registration(db, registration_id, client_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="registration not found")


@router.post("/{registration_id}/claim", response_model=RegistrationRead)
async def claim_registration_route(
    registration_id: int,
    client_id: str = Query(...),
    db: AsyncSession = Depends(get_session),
):
    registration = await claim_registration(db, registration_id, client_id)
    if registration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="registration not found")
    return registration
