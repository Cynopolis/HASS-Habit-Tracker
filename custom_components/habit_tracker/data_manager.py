"""Data manager for habit tracker - handles persistence and data operations."""

import logging
from typing import Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    KEY_COMPLETIONS,
    KEY_HABITS,
    KEY_NAME,
    default_habit_data,
    get_current_week_dates,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "habit_tracker_data"


class DataManager:
    """Manages habit tracker data storage and operations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the data manager using HA's Store helper."""
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}
        self._load_sync()

    def _load_sync(self) -> None:
        """Load data from disk synchronously (called during __init__)."""
        try:
            loaded = self._store.data
            if loaded is not None:
                self._data = loaded
                _LOGGER.debug("Loaded habit tracker data from store")
            else:
                self._data = {}
        except Exception as e:
            _LOGGER.error("Failed to load habit tracker data: %s", e)
            self._data = {}

    async def _async_save(self) -> None:
        """Save data to disk asynchronously."""
        try:
            await self._store.async_save(self._data)
            _LOGGER.debug("Saved habit tracker data to store")
        except Exception as e:
            _LOGGER.error("Failed to save habit tracker data: %s", e)

    def save_sync(self) -> None:
        """Save data synchronously (blocking, use sparingly)."""
        try:
            self._store.save(self._data)
            _LOGGER.debug("Saved habit tracker data to store")
        except Exception as e:
            _LOGGER.error("Failed to save habit tracker data: %s", e)

    @property
    def people(self) -> dict[str, dict]:
        """Get all people data."""
        return self._data.get("people", {})

    @property
    def person_keys(self) -> list[str]:
        """Get all person keys."""
        return list(self.people.keys())

    def get_person_data(self, person_key: str) -> Optional[dict]:
        """Get data for a specific person."""
        return self.people.get(person_key)

    def add_person(self, person_key: str, name: str) -> dict:
        """Add a new person's habit tracker."""
        if person_key in self.people:
            _LOGGER.warning("Person '%s' already exists", person_key)
            return self.people[person_key]

        person_data = {
            KEY_NAME: name,
            KEY_HABITS: [],
        }
        self._data.setdefault("people", {})[person_key] = person_data
        self.save_sync()
        _LOGGER.info("Added new person '%s' (%s)", name, person_key)
        return person_data

    def remove_person(self, person_key: str) -> bool:
        """Remove a person's habit tracker."""
        if person_key not in self.people:
            _LOGGER.warning("Person '%s' does not exist", person_key)
            return False

        del self._data["people"][person_key]
        self.save_sync()
        _LOGGER.info("Removed person '%s'", person_key)
        return True

    def get_habit(self, person_key: str, habit_id: str) -> Optional[dict]:
        """Get a specific habit for a person."""
        person = self.get_person_data(person_key)
        if not person:
            return None
        for habit in person.get(KEY_HABITS, []):
            if habit["id"] == habit_id:
                return habit
        return None

    def add_habit(self, person_key: str, habit_id: str, name: str) -> Optional[dict]:
        """Add a new habit for a person."""
        person = self.get_person_data(person_key)
        if not person:
            _LOGGER.error("Person '%s' does not exist", person_key)
            return None

        # Check if habit already exists
        if self.get_habit(person_key, habit_id):
            _LOGGER.warning(
                "Habit '%s' already exists for person '%s'", habit_id, person_key
            )
            return None

        habit = default_habit_data(habit_id, name)
        person[KEY_HABITS].append(habit)
        self.save_sync()
        _LOGGER.info(
            "Added habit '%s' (%s) for person '%s'", name, habit_id, person_key
        )
        return habit

    def remove_habit(self, person_key: str, habit_id: str) -> bool:
        """Remove a habit from a person."""
        person = self.get_person_data(person_key)
        if not person:
            return False

        habits = person.get(KEY_HABITS, [])
        for i, habit in enumerate(habits):
            if habit["id"] == habit_id:
                person[KEY_HABITS].pop(i)
                self.save_sync()
                _LOGGER.info(
                    "Removed habit '%s' from person '%s'", habit_id, person_key
                )
                return True
        return False

    def set_completion(
        self, person_key: str, habit_id: str, date_str: str, completed: bool
    ) -> bool:
        """Set completion status for a habit on a specific date."""
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            _LOGGER.error("Habit '%s' not found for person '%s'", habit_id, person_key)
            return False

        completions = habit.setdefault(KEY_COMPLETIONS, {})
        old_value = completions.get(date_str)
        completions[date_str] = completed
        self.save_sync()

        status = "completed" if completed else "not completed"
        _LOGGER.debug(
            "Set %s for '%s' on %s (was: %s)",
            status,
            habit["name"],
            date_str,
            old_value,
        )
        return True

    def get_completion(
        self, person_key: str, habit_id: str, date_str: str
    ) -> Optional[bool]:
        """Get completion status for a habit on a specific date."""
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            return None
        return habit.get(KEY_COMPLETIONS, {}).get(date_str)

    def get_total_completed(self, person_key: str, habit_id: str) -> int:
        """Get total number of days a habit has been completed."""
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            return 0
        return sum(1 for v in habit.get(KEY_COMPLETIONS, {}).values() if v)

    def get_completion_rate(self, person_key: str, habit_id: str) -> float:
        """Get completion rate as a percentage (0-100)."""
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            return 0.0

        completions = habit.get(KEY_COMPLETIONS, {})
        if not completions:
            return 0.0

        completed_count = sum(1 for v in completions.values() if v)
        total_days = len(completions)
        return round((completed_count / total_days) * 100, 1)

    def get_week_completions(self, person_key: str, habit_id: str) -> dict[str, bool]:
        """Get completion status for a habit for the current week."""
        week_dates = get_current_week_dates()
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            return {d: False for d in week_dates}

        completions = habit.get(KEY_COMPLETIONS, {})
        return {d: completions.get(d, False) for d in week_dates}

    def reset_week(self, person_key: str) -> int:
        """Reset all habits for the current week (uncheck all)."""
        week_dates = get_current_week_dates()
        person = self.get_person_data(person_key)
        if not person:
            return 0

        reset_count = 0
        for habit in person.get(KEY_HABITS, []):
            completions = habit.setdefault(KEY_COMPLETIONS, {})
            for date_str in week_dates:
                if completions.get(date_str, False):
                    completions[date_str] = False
                    reset_count += 1

        self.save_sync()
        _LOGGER.info("Reset %s completions for person '%s'", reset_count, person_key)
        return reset_count

    def get_person_habits(self, person_key: str) -> list[dict]:
        """Get all habits for a person."""
        person = self.get_person_data(person_key)
        if not person:
            return []
        return person.get(KEY_HABITS, [])

    def get_all_habits(self) -> dict[str, list[dict]]:
        """Get all habits for all people."""
        result = {}
        for key in self.person_keys:
            result[key] = self.get_person_habits(key)
        return result
