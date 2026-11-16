from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import require_admin
from database.session import get_session
from schemas.dish import DishAdmin, DishCreate, DishUpdate
from schemas.proposal import ProposalApprove, ProposalRead
from schemas.registration import (
    AttendanceGroup,
    RegistrationRead,
    RegistrationReassign,
)
from services.dish_service import (
    create_dish,
    deactivate_dish,
    list_admin as list_dishes_admin,
    update_dish,
)
from services.proposal_service import (
    approve_proposal,
    list_all as list_proposals_all,
    list_pending,
    reject_proposal,
)
from services.registration_service import (
    delete_registration,
    list_all as list_registrations_all,
    list_attendance_grouped,
    reassign_registration,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# --- Dishes ---
@router.get("/dishes", response_model=list[DishAdmin])
async def admin_list_dishes(db: AsyncSession = Depends(get_session)):
    return await list_dishes_admin(db)


@router.post("/dishes", response_model=DishAdmin, status_code=status.HTTP_201_CREATED)
async def admin_create_dish(payload: DishCreate, db: AsyncSession = Depends(get_session)):
    return await create_dish(db, payload)


@router.patch("/dishes/{dish_id}", response_model=DishAdmin)
async def admin_update_dish(
    dish_id: int, payload: DishUpdate, db: AsyncSession = Depends(get_session)
):
    result = await update_dish(db, dish_id, payload)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dish not found")
    return result


@router.post("/dishes/{dish_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def admin_deactivate_dish(dish_id: int, db: AsyncSession = Depends(get_session)):
    ok = await deactivate_dish(db, dish_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dish not found")


# --- Proposals ---
@router.get("/proposals", response_model=list[ProposalRead])
async def admin_list_proposals(
    status_filter: str | None = Query(default="pending", alias="status"),
    db: AsyncSession = Depends(get_session),
):
    if status_filter == "all":
        return await list_proposals_all(db)
    if status_filter == "pending":
        return await list_pending(db)
    # allow filtering by specific status
    all_items = await list_proposals_all(db)
    return [p for p in all_items if p.status == status_filter]


@router.post("/proposals/{proposal_id}/approve", response_model=DishAdmin)
async def admin_approve_proposal(
    proposal_id: int,
    payload: ProposalApprove,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await approve_proposal(db, proposal_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/proposals/{proposal_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def admin_reject_proposal(proposal_id: int, db: AsyncSession = Depends(get_session)):
    ok = await reject_proposal(db, proposal_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="proposal not found or not pending")


# --- Registrations / attendance ---
@router.get("/registrations", response_model=list[RegistrationRead])
async def admin_list_registrations(db: AsyncSession = Depends(get_session)):
    return await list_registrations_all(db)


@router.get("/attendance", response_model=list[AttendanceGroup])
async def admin_attendance(db: AsyncSession = Depends(get_session)):
    groups = await list_attendance_grouped(db)
    return [AttendanceGroup(**g) for g in groups]


@router.delete("/registrations/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_registration(
    registration_id: int, db: AsyncSession = Depends(get_session)
):
    ok = await delete_registration(db, registration_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="registration not found")


@router.patch("/registrations/{registration_id}", response_model=RegistrationRead)
async def admin_reassign_registration(
    registration_id: int,
    payload: RegistrationReassign,
    db: AsyncSession = Depends(get_session),
):
    try:
        result = await reassign_registration(db, registration_id, payload.new_dish_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="registration not found")
    return result
