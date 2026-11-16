from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from schemas.proposal import ProposalCreate, ProposalRead
from services.proposal_service import create_proposal

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
async def post_proposal(
    payload: ProposalCreate, db: AsyncSession = Depends(get_session)
):
    return await create_proposal(db, payload)
