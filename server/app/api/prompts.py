import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import require_owner
from app.services.stats import build_summary, load_practice_data

router = APIRouter(
    prefix="/prompts",
    tags=["prompts"],
    dependencies=[Depends(require_owner)],
)


@router.get("/practice-summary")
async def practice_summary_prompt(db: AsyncSession = Depends(get_db)) -> dict:
    summary = build_summary(await load_practice_data(db))
    prompt = (
        "You are helping analyze a golf chipping practice log. "
        "Use the JSON summary below to identify volume trends, Target Completion strengths, "
        "weak targets, and a simple next-practice plan. Keep recommendations specific and "
        "grounded in the data.\n\n"
        f"{json.dumps(summary, indent=2)}"
    )
    return {"prompt": prompt, "summary": summary}
