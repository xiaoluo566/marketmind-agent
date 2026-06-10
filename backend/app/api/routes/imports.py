from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.imports.review_importer import import_reviews
from app.imports.schemas import ReviewImportRequest
from app.storage.database import get_db_session

router = APIRouter()


@router.post("/imports/reviews", status_code=status.HTTP_201_CREATED)
def import_review_file(
    payload: ReviewImportRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict:
    result = import_reviews(
        session=session,
        payload=payload,
        trace_id=request.state.trace_id,
    )
    session.commit()
    return success_response(
        data=result.model_dump(mode="json"),
        message="imported",
        trace_id=request.state.trace_id,
    )

