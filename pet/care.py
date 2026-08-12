from __future__ import annotations

from datetime import timedelta

from .i18n import tr


def format_care_duration(language: str, elapsed: timedelta) -> str:
    """Format elapsed care time with at most the two most useful units."""
    total_minutes = max(0, int(elapsed.total_seconds() // 60))
    if total_minutes < 60:
        return tr(language, "duration_minutes", minutes=total_minutes)

    total_hours, minutes = divmod(total_minutes, 60)
    if total_hours < 24:
        return tr(
            language,
            "duration_hours_minutes",
            hours=total_hours,
            minutes=minutes,
        )

    days, hours = divmod(total_hours, 24)
    return tr(language, "duration_days_hours", days=days, hours=hours)
