import csv
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import require_owner
from app.services.stats import build_export_payload, build_summary, load_practice_data

router = APIRouter(
    prefix="/export",
    tags=["export"],
    dependencies=[Depends(require_owner)],
)


async def _export_payload(db: AsyncSession) -> dict:
    data = await load_practice_data(db)
    summary = build_summary(data)
    return build_export_payload(data, summary)


@router.get("/json")
async def export_json(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    return JSONResponse(
        await _export_payload(db),
        headers={"Content-Disposition": 'attachment; filename="chip-tracker-export.json"'},
    )


@router.get("/csv")
async def export_csv(db: AsyncSession = Depends(get_db)) -> Response:
    payload = await _export_payload(db)
    output = StringIO()
    fieldnames = [
        "record_type",
        "id",
        "session_id",
        "game_run_id",
        "bucket_id",
        "started_at",
        "ended_at",
        "status",
        "variant",
        "target_number",
        "attempts",
        "hit",
        "ball_count",
        "source",
        "club",
        "distance_ft",
        "action",
        "event_index",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for session in payload["sessions"]:
        writer.writerow(
            {
                "record_type": "session",
                "id": session["id"],
                "session_id": session["id"],
                "started_at": session["started_at"],
                "ended_at": session["ended_at"],
                "status": session["status"],
                "club": session["default_club"],
                "distance_ft": session["default_distance_ft"],
            }
        )

    for bucket in payload["buckets"]:
        writer.writerow(
            {
                "record_type": "bucket",
                "id": bucket["id"],
                "session_id": bucket["session_id"],
                "game_run_id": bucket["game_run_id"],
                "bucket_id": bucket["id"],
                "started_at": bucket["started_at"],
                "ended_at": bucket["ended_at"],
                "status": bucket["status"],
                "ball_count": bucket["ball_count"],
                "source": bucket["source"],
                "club": bucket["club"],
                "distance_ft": bucket["distance_ft"],
            }
        )

    for game in payload["game_runs"]:
        writer.writerow(
            {
                "record_type": "game_run",
                "id": game["id"],
                "session_id": game["session_id"],
                "game_run_id": game["id"],
                "started_at": game["started_at"],
                "ended_at": game["ended_at"],
                "status": game["status"],
                "variant": game["variant"],
            }
        )

    for target in payload["target_completion_targets"]:
        writer.writerow(
            {
                "record_type": "target",
                "id": target["id"],
                "game_run_id": target["game_run_id"],
                "target_number": target["target_number"],
                "attempts": target["attempts"],
                "hit": target["hit"],
            }
        )

    for event in payload["target_completion_events"]:
        writer.writerow(
            {
                "record_type": "event",
                "id": event["id"],
                "game_run_id": event["game_run_id"],
                "bucket_id": event["bucket_id"],
                "target_number": event["target_number"],
                "action": event["action"],
                "event_index": event["event_index"],
                "started_at": event["created_at"],
            }
        )

    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="chip-tracker-export.csv"'},
    )
