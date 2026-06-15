\"\"\"Central scheduler for timed tasks, reminders and proactive messages.\"\"\"

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger


class TaskScheduler:
    \"\"\"Manages all scheduled tasks using APScheduler.\"\"\"

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks: dict[str, Any] = {}

    def start(self) -> None:
        self.scheduler.start()
        logger.info("Task scheduler started")

    def stop(self) -> None:
        self.scheduler.shutdown(wait=False)
        logger.info("Task scheduler stopped")

    def add_interval_task(self, task_id: str, func: Callable,
                          hours: float = 0, minutes: float = 0,
                          **kwargs) -> None:
        \"\"\"Add a repeating task.\"\"\"
        self.scheduler.add_job(
            func,
            "interval",
            id=task_id,
            hours=hours,
            minutes=minutes,
            replace_existing=True,
            **kwargs,
        )
        logger.info("Scheduled interval task '{}': every {}h{}m", task_id, hours, minutes)

    def add_cron_task(self, task_id: str, func: Callable,
                      hour: int, minute: int = 0, **kwargs) -> None:
        \"\"\"Add a cron-style daily task.\"\"\"
        self.scheduler.add_job(
            func,
            "cron",
            id=task_id,
            hour=hour,
            minute=minute,
            replace_existing=True,
            **kwargs,
        )
        logger.info("Scheduled cron task '{}': {:02d}:{:02d}", task_id, hour, minute)

    def add_daily_time_range_task(self, task_id: str, func: Callable,
                                  hour_from: int, hour_to: int,
                                  interval_minutes: int = 60) -> None:
        \"\"\"Add a task that runs during a time window.\"\"\"
        self.scheduler.add_job(
            func,
            "interval",
            id=task_id,
            minutes=interval_minutes,
            start_date=f"2024-01-01 {hour_from:02d}:00:00",
            end_date=f"2024-01-01 {hour_to:02d}:00:00",
            replace_existing=True,
        )
        logger.info(
            "Scheduled range task '{}': {}:00-{}:00 every {}min",
            task_id, hour_from, hour_to, interval_minutes,
        )

    def remove_task(self, task_id: str) -> None:
        try:
            self.scheduler.remove_job(task_id)
            logger.info("Removed task '{}'", task_id)
        except Exception:
            pass

    @property
    def running(self) -> bool:
        return self.scheduler.running
