from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.models.card_progress import CardProgress


EASE_DELTAS = {
    0: -0.30,
    1: -0.15,
    2: 0.00,
    3: 0.10,
    4: 0.20,
}

QUALITY_BONUS = {
    2: 0.90,
    3: 1.00,
    4: 1.15,
}

MIN_EASE = 1.3
MAX_EASE = 3.0


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def apply_srs_answer(progress: CardProgress, quality: int, now: datetime | None = None) -> CardProgress:
    if quality < 0 or quality > 4:
        raise ValueError("quality must be between 0 and 4")

    now = now or utcnow()

    new_ease = progress.ease + EASE_DELTAS[quality]
    new_ease = max(MIN_EASE, min(MAX_EASE, new_ease))

    repetitions = progress.repetitions
    interval_days = progress.interval_days

    if quality <= 1:
        repetitions = 0
        interval_days = 0
        last_answer_correct = False
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 3
        else:
            interval_days = round(interval_days * new_ease * QUALITY_BONUS[quality])
            interval_days = max(1, interval_days)

        repetitions += 1
        last_answer_correct = True

    progress.ease = new_ease
    progress.repetitions = repetitions
    progress.interval_days = interval_days
    progress.last_answered_at = now
    progress.last_answer_correct = last_answer_correct
    progress.due_at = now + timedelta(days=interval_days)

    return progress