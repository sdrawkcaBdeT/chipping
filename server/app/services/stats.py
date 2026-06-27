from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
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


def _average_seconds(values: list[int]) -> int | None:
    if not values:
        return None
    return int(round(sum(values) / len(values)))


def _balls_in_last_days(
    daily_totals: dict[str, dict[str, int]],
    today: date,
    days: int,
) -> int:
    start_date = today - timedelta(days=days - 1)
    return sum(
        values["balls"]
        for date_key, values in daily_totals.items()
        if date.fromisoformat(date_key) >= start_date
    )


def _datetime_key(value: datetime) -> datetime:
    return value.replace(tzinfo=None)


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
    today = datetime.now(timezone.utc).date()

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
    completed_session_ball_counts = [
        summary["ball_count"]
        for summary in session_summaries
        if summary["status"] == "completed"
    ]
    completed_session_durations = [
        summary["duration_seconds"]
        for summary in session_summaries
        if summary["status"] == "completed" and summary["duration_seconds"] is not None
    ]
    latest_practice_at = max(
        [bucket.started_at for bucket in buckets] + [session.started_at for session in sessions],
        key=_datetime_key,
        default=None,
    )

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
    latest_completed_run = completed_completion_runs[0] if completed_completion_runs else None
    previous_completed_run = (
        completed_completion_runs[1] if len(completed_completion_runs) > 1 else None
    )

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

    target_stats_with_hits = [
        target for target in target_stats if target["average_balls_to_hit"] is not None
    ]
    hardest_targets = sorted(
        target_stats_with_hits,
        key=lambda target: (
            target["average_balls_to_hit"] or 0,
            target["attempts"],
        ),
        reverse=True,
    )[:3]
    easiest_targets = sorted(
        target_stats_with_hits,
        key=lambda target: (
            target["average_balls_to_hit"] or 0,
            -target["attempts"],
        ),
    )[:3]

    return {
        "overview": {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed_sessions),
            "active_sessions": len(active_sessions),
            "total_balls": total_balls,
            "bucket_count": len(buckets),
            "practice_days": len(daily_totals),
            "balls_last_7_days": _balls_in_last_days(daily_totals, today, 7),
            "balls_last_30_days": _balls_in_last_days(daily_totals, today, 30),
            "average_balls_per_completed_session": _average(completed_session_ball_counts),
            "average_completed_session_duration_seconds": _average_seconds(
                completed_session_durations
            ),
            "target_completion_runs": len(games),
            "completed_target_completion_runs": len(completed_completion_runs),
            "best_completion_score": min(completed_scores) if completed_scores else None,
            "median_completion_score": median(completed_scores) if completed_scores else None,
            "latest_session_at": _iso(sessions[0].started_at) if sessions else None,
            "latest_practice_at": _iso(latest_practice_at),
        },
        "volume": {
            "total_balls": total_balls,
            "bucket_count": len(buckets),
            "practice_days": len(daily_totals),
            "balls_last_7_days": _balls_in_last_days(daily_totals, today, 7),
            "balls_last_30_days": _balls_in_last_days(daily_totals, today, 30),
            "average_balls_per_practice_day": _average(
                [values["balls"] for values in daily_totals.values()]
            ),
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
            "hardest_targets": hardest_targets,
            "easiest_targets": easiest_targets,
        },
        "completion": {
            "runs": completion_runs,
            "completed_runs": completed_completion_runs,
            "completed_count": len(completed_completion_runs),
            "best_score": min(completed_scores) if completed_scores else None,
            "median_score": median(completed_scores) if completed_scores else None,
            "average_score": _average(completed_scores),
            "latest_score": latest_completed_run["score"] if latest_completed_run else None,
            "latest_completed_at": (
                latest_completed_run["ended_at"] if latest_completed_run else None
            ),
            "score_delta_from_previous": (
                latest_completed_run["score"] - previous_completed_run["score"]
                if latest_completed_run and previous_completed_run
                else None
            ),
            "variant_comparison": {
                variant: {
                    "completed_runs": len(scores),
                    "best_score": min(scores) if scores else None,
                    "median_score": median(scores) if scores else None,
                    "average_score": _average(scores),
                }
                for variant, scores in sorted(variant_scores.items())
            },
        },
        "sessions": {
            "sessions": session_summaries,
        },
    }


def build_session_detail(data: dict[str, list[Any]], session_id: str) -> dict[str, Any] | None:
    sessions: list[PracticeSession] = data["sessions"]
    buckets: list[PracticeBucket] = data["buckets"]
    games: list[GameRun] = data["games"]
    targets: list[TargetCompletionTarget] = data["targets"]

    session = next((item for item in sessions if item.id == session_id), None)
    if session is None:
        return None

    session_buckets = [
        bucket
        for bucket in buckets
        if bucket.session_id == session.id
    ]
    session_games = [
        game
        for game in games
        if game.session_id == session.id
    ]

    buckets_by_game: dict[str, list[PracticeBucket]] = defaultdict(list)
    targets_by_game: dict[str, list[TargetCompletionTarget]] = defaultdict(list)
    for bucket in session_buckets:
        if bucket.game_run_id:
            buckets_by_game[bucket.game_run_id].append(bucket)
    for target in targets:
        targets_by_game[target.game_run_id].append(target)

    source_totals: dict[str, int] = defaultdict(int)
    for bucket in session_buckets:
        source_totals[bucket.source] += bucket.ball_count

    games_payload = []
    for game in sorted(session_games, key=lambda item: _datetime_key(item.started_at)):
        game_targets = sorted(targets_by_game[game.id], key=lambda target: target.order_index)
        score = sum(target.attempts for target in game_targets)
        games_payload.append(
            {
                "id": game.id,
                "game_type": game.game_type,
                "variant": game.variant,
                "status": game.status,
                "started_at": _iso(game.started_at),
                "ended_at": _iso(game.ended_at),
                "duration_seconds": _duration_seconds(game.started_at, game.ended_at),
                "score": score,
                "completed_target_count": sum(1 for target in game_targets if target.hit),
                "target_order": game.target_order,
                "bucket_count": len(buckets_by_game[game.id]),
                "targets": [
                    {
                        "target_number": target.target_number,
                        "order_index": target.order_index,
                        "attempts": target.attempts,
                        "hit": target.hit,
                        "completed_at": _iso(target.completed_at),
                    }
                    for target in game_targets
                ],
            }
        )

    return {
        "session": {
            "id": session.id,
            "started_at": _iso(session.started_at),
            "ended_at": _iso(session.ended_at),
            "status": session.status,
            "duration_seconds": _duration_seconds(session.started_at, session.ended_at),
            "ball_count": sum(bucket.ball_count for bucket in session_buckets),
            "bucket_count": len(session_buckets),
            "game_count": len(session_games),
            "default_club": session.default_club,
            "default_distance_ft": session.default_distance_ft,
        },
        "buckets": [
            {
                "id": bucket.id,
                "game_run_id": bucket.game_run_id,
                "ball_count": bucket.ball_count,
                "club": bucket.club,
                "distance_ft": bucket.distance_ft,
                "source": bucket.source,
                "status": bucket.status,
                "started_at": _iso(bucket.started_at),
                "ended_at": _iso(bucket.ended_at),
            }
            for bucket in sorted(session_buckets, key=lambda item: _datetime_key(item.started_at))
        ],
        "games": games_payload,
        "source_totals": dict(sorted(source_totals.items())),
        "provenance": {
            "design_version": "v0-manual-tracker",
            "app_git_sha": None,
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
