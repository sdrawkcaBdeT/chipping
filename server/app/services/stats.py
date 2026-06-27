from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    GameRun,
    PracticeBucket,
    PracticeSession,
    TargetCompletionEvent,
    TargetCompletionTarget,
)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _duration_seconds(start: datetime | None, end: datetime | None) -> int | None:
    if start is None:
        return None

    effective_end = end or datetime.now(timezone.utc)
    if start.tzinfo is None and effective_end.tzinfo is not None:
        effective_end = effective_end.replace(tzinfo=None)
    if start.tzinfo is not None and effective_end.tzinfo is None:
        effective_end = effective_end.replace(tzinfo=timezone.utc)

    return max(0, int((effective_end - start).total_seconds()))


def _average(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


async def load_practice_data(db: AsyncSession) -> dict[str, list[Any]]:
    sessions_result = await db.execute(
        select(PracticeSession).order_by(PracticeSession.started_at.desc(), PracticeSession.id)
    )
    buckets_result = await db.execute(
        select(PracticeBucket).order_by(PracticeBucket.started_at.desc(), PracticeBucket.id)
    )
    games_result = await db.execute(
        select(GameRun).order_by(GameRun.started_at.desc(), GameRun.id)
    )
    targets_result = await db.execute(
        select(TargetCompletionTarget).order_by(
            TargetCompletionTarget.game_run_id,
            TargetCompletionTarget.order_index,
        )
    )
    events_result = await db.execute(
        select(TargetCompletionEvent).order_by(
            TargetCompletionEvent.game_run_id,
            TargetCompletionEvent.event_index,
        )
    )

    return {
        "sessions": list(sessions_result.scalars().all()),
        "buckets": list(buckets_result.scalars().all()),
        "games": list(games_result.scalars().all()),
        "targets": list(targets_result.scalars().all()),
        "events": list(events_result.scalars().all()),
    }


def build_summary(data: dict[str, list[Any]]) -> dict[str, Any]:
    sessions: list[PracticeSession] = data["sessions"]
    buckets: list[PracticeBucket] = data["buckets"]
    games: list[GameRun] = data["games"]
    targets: list[TargetCompletionTarget] = data["targets"]
    events: list[TargetCompletionEvent] = data["events"]

    buckets_by_session: dict[str, list[PracticeBucket]] = defaultdict(list)
    buckets_by_game: dict[str, list[PracticeBucket]] = defaultdict(list)
    games_by_session: dict[str, list[GameRun]] = defaultdict(list)
    targets_by_game: dict[str, list[TargetCompletionTarget]] = defaultdict(list)

    for bucket in buckets:
        buckets_by_session[bucket.session_id].append(bucket)
        if bucket.game_run_id:
            buckets_by_game[bucket.game_run_id].append(bucket)

    for game in games:
        games_by_session[game.session_id].append(game)

    for target in targets:
        targets_by_game[target.game_run_id].append(target)

    total_balls = sum(bucket.ball_count for bucket in buckets)
    completed_sessions = [session for session in sessions if session.status == "completed"]
    active_sessions = [session for session in sessions if session.status == "active"]

    source_totals: dict[str, int] = defaultdict(int)
    daily_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"balls": 0, "buckets": 0})
    for bucket in buckets:
        source_totals[bucket.source] += bucket.ball_count
        day_key = bucket.started_at.date().isoformat()
        daily_totals[day_key]["balls"] += bucket.ball_count
        daily_totals[day_key]["buckets"] += 1

    session_summaries = [
        {
            "id": session.id,
            "started_at": _iso(session.started_at),
            "ended_at": _iso(session.ended_at),
            "status": session.status,
            "duration_seconds": _duration_seconds(session.started_at, session.ended_at),
            "ball_count": sum(bucket.ball_count for bucket in buckets_by_session[session.id]),
            "bucket_count": len(buckets_by_session[session.id]),
            "game_count": len(games_by_session[session.id]),
            "default_club": session.default_club,
            "default_distance_ft": session.default_distance_ft,
        }
        for session in sessions
    ]

    completion_runs = []
    for game in games:
        game_targets = sorted(targets_by_game[game.id], key=lambda target: target.order_index)
        score = sum(target.attempts for target in game_targets)
        completed_targets = [target.target_number for target in game_targets if target.hit]
        completion_runs.append(
            {
                "id": game.id,
                "session_id": game.session_id,
                "variant": game.variant,
                "status": game.status,
                "started_at": _iso(game.started_at),
                "ended_at": _iso(game.ended_at),
                "duration_seconds": _duration_seconds(game.started_at, game.ended_at),
                "score": score,
                "completed_target_count": len(completed_targets),
                "completed_targets": completed_targets,
                "target_order": game.target_order,
                "bucket_count": len(buckets_by_game[game.id]),
            }
        )

    completed_completion_runs = [
        run for run in completion_runs if run["status"] == "completed" and run["score"] > 0
    ]
    completed_scores = [run["score"] for run in completed_completion_runs]

    variant_scores: dict[str, list[int]] = defaultdict(list)
    for run in completed_completion_runs:
        variant_scores[run["variant"]].append(run["score"])

    target_stats = []
    for target_number in range(1, 10):
        target_rows = [target for target in targets if target.target_number == target_number]
        hit_rows = [target for target in target_rows if target.hit]
        hit_attempts = [target.attempts for target in hit_rows]
        attempts = sum(target.attempts for target in target_rows)
        hits = len(hit_rows)
        target_stats.append(
            {
                "target_number": target_number,
                "attempts": attempts,
                "hits": hits,
                "misses": max(0, attempts - hits),
                "hit_rate": round(hits / attempts, 3) if attempts else None,
                "average_balls_to_hit": _average(hit_attempts),
                "median_balls_to_hit": median(hit_attempts) if hit_attempts else None,
                "best_balls_to_hit": min(hit_attempts) if hit_attempts else None,
            }
        )

    event_count = len(events)
    hit_count = sum(1 for event in events if event.action == "hit")
    miss_count = sum(1 for event in events if event.action == "miss")

    return {
        "overview": {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed_sessions),
            "active_sessions": len(active_sessions),
            "total_balls": total_balls,
            "bucket_count": len(buckets),
            "target_completion_runs": len(games),
            "completed_target_completion_runs": len(completed_completion_runs),
            "best_completion_score": min(completed_scores) if completed_scores else None,
            "median_completion_score": median(completed_scores) if completed_scores else None,
            "latest_session_at": _iso(sessions[0].started_at) if sessions else None,
        },
        "volume": {
            "total_balls": total_balls,
            "bucket_count": len(buckets),
            "source_totals": dict(sorted(source_totals.items())),
            "daily": [
                {"date": date, **values}
                for date, values in sorted(daily_totals.items(), reverse=True)
            ],
        },
        "accuracy": {
            "target_completion_attempts": event_count,
            "hits": hit_count,
            "misses": miss_count,
            "hit_rate": round(hit_count / event_count, 3) if event_count else None,
        },
        "targets": {
            "targets": target_stats,
        },
        "completion": {
            "runs": completion_runs,
            "completed_runs": completed_completion_runs,
            "best_score": min(completed_scores) if completed_scores else None,
            "median_score": median(completed_scores) if completed_scores else None,
            "average_score": _average(completed_scores),
            "variant_comparison": {
                variant: {
                    "completed_runs": len(scores),
                    "best_score": min(scores) if scores else None,
                    "average_score": _average(scores),
                }
                for variant, scores in sorted(variant_scores.items())
            },
        },
        "sessions": {
            "sessions": session_summaries,
        },
    }


def build_export_payload(data: dict[str, list[Any]], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "sessions": [
            {
                "id": session.id,
                "started_at": _iso(session.started_at),
                "ended_at": _iso(session.ended_at),
                "status": session.status,
                "default_club": session.default_club,
                "default_distance_ft": session.default_distance_ft,
                "notes": session.notes,
                "created_at": _iso(session.created_at),
                "updated_at": _iso(session.updated_at),
            }
            for session in data["sessions"]
        ],
        "buckets": [
            {
                "id": bucket.id,
                "session_id": bucket.session_id,
                "game_run_id": bucket.game_run_id,
                "ball_count": bucket.ball_count,
                "club": bucket.club,
                "distance_ft": bucket.distance_ft,
                "source": bucket.source,
                "status": bucket.status,
                "started_at": _iso(bucket.started_at),
                "ended_at": _iso(bucket.ended_at),
                "created_at": _iso(bucket.created_at),
                "updated_at": _iso(bucket.updated_at),
            }
            for bucket in data["buckets"]
        ],
        "game_runs": [
            {
                "id": game.id,
                "session_id": game.session_id,
                "game_type": game.game_type,
                "variant": game.variant,
                "status": game.status,
                "target_order": game.target_order,
                "started_at": _iso(game.started_at),
                "ended_at": _iso(game.ended_at),
                "created_at": _iso(game.created_at),
                "updated_at": _iso(game.updated_at),
            }
            for game in data["games"]
        ],
        "target_completion_targets": [
            {
                "id": target.id,
                "game_run_id": target.game_run_id,
                "target_number": target.target_number,
                "order_index": target.order_index,
                "attempts": target.attempts,
                "hit": target.hit,
                "completed_at": _iso(target.completed_at),
                "created_at": _iso(target.created_at),
                "updated_at": _iso(target.updated_at),
            }
            for target in data["targets"]
        ],
        "target_completion_events": [
            {
                "id": event.id,
                "game_run_id": event.game_run_id,
                "bucket_id": event.bucket_id,
                "target_number": event.target_number,
                "action": event.action,
                "event_index": event.event_index,
                "created_at": _iso(event.created_at),
            }
            for event in data["events"]
        ],
    }
