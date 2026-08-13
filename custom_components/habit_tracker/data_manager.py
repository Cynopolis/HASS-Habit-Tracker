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
        _LOGGER.debug("DataManager.__init__ called")
        self.hass = hass
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}
        _LOGGER.debug("Store initialized with key: %s", STORAGE_KEY)

    async def async_load(self) -> None:
        """Load data from disk asynchronously."""
        _LOGGER.debug("async_load called, store key: %s", STORAGE_KEY)
        try:
            loaded = await self._store.async_load()
            _LOGGER.debug("Store returned: %s", loaded is not None)
            if loaded is not None:
                self._data = loaded
                _LOGGER.debug(
                    "Loaded habit tracker data from store, people: %s",
                    list(self._data.get("people", {}).keys()),
                )
            else:
                self._data = {}
                _LOGGER.debug("No existing data in store, initializing empty dict")
        except Exception as e:
            _LOGGER.error("Failed to load habit tracker data: %s", e, exc_info=True)
            self._data = {}

    async def async_save(self) -> None:
        """Save data to disk asynchronously."""
        _LOGGER.debug("async_save called, data keys: %s", list(self._data.keys()))
        try:
            await self._store.async_save(self._data)
            _LOGGER.debug("Saved habit tracker data to store successfully")
        except Exception as e:
            _LOGGER.error("Failed to save habit tracker data: %s", e, exc_info=True)

    @property
    def people(self) -> dict[str, dict]:
        """Get all people data."""
        result = self._data.get("people", {})
        _LOGGER.debug(
            "people property accessed, returning %d people: %s",
            len(result),
            list(result.keys()),
        )
        return result

    @property
    def person_keys(self) -> list[str]:
        """Get all person keys."""
        result = list(self.people.keys())
        _LOGGER.debug("person_keys property accessed, returning: %s", result)
        return result

    def get_person_data(self, person_key: str) -> Optional[dict]:
        """Get data for a specific person."""
        _LOGGER.debug("get_person_data called for '%s'", person_key)
        result = self.people.get(person_key)
        _LOGGER.debug("get_person_data returning: %s", result is not None)
        return result

    def add_person(self, person_key: str, name: str) -> dict:
        """Add a new person's habit tracker."""
        _LOGGER.debug("add_person called for key='%s', name='%s'", person_key, name)
        if person_key in self.people:
            _LOGGER.warning("Person '%s' already exists", person_key)
            return self.people[person_key]

        person_data = {
            KEY_NAME: name,
            KEY_HABITS: [],
        }
        self._data.setdefault("people", {})[person_key] = person_data
        _LOGGER.debug("Person '%s' added successfully", person_key)
        return person_data

    def remove_person(self, person_key: str) -> bool:
        """Remove a person's habit tracker."""
        _LOGGER.debug("remove_person called for '%s'", person_key)
        if person_key not in self.people:
            _LOGGER.warning("Person '%s' does not exist", person_key)
            return False

        del self._data["people"][person_key]
        _LOGGER.debug("Person '%s' removed successfully", person_key)
        return True

    def get_habit(self, person_key: str, habit_id: str) -> Optional[dict]:
        """Get a specific habit for a person."""
        _LOGGER.debug(
            "get_habit called for person='%s', habit_id='%s'", person_key, habit_id
        )
        person = self.get_person_data(person_key)
        if not person:
            _LOGGER.debug("Person '%s' not found", person_key)
            return None
        for habit in person.get(KEY_HABITS, []):
            if habit["id"] == habit_id:
                _LOGGER.debug("Found habit: %s", habit.get(KEY_NAME))
                return habit
        _LOGGER.debug("Habit '%s' not found for person '%s'", habit_id, person_key)
        return None

    def add_habit(self, person_key: str, habit_id: str, name: str) -> Optional[dict]:
        """Add a new habit for a person."""
        _LOGGER.debug(
            "add_habit called for person='%s', habit_id='%s', name='%s'",
            person_key,
            habit_id,
            name,
        )
        person = self.get_person_data(person_key)
        if not person:
            _LOGGER.error("Person '%s' does not exist", person_key)
            return None

        # Check if habit already exists
        existing = self.get_habit(person_key, habit_id)
        if existing:
            _LOGGER.warning(
                "Habit '%s' already exists for person '%s'", habit_id, person_key
            )
            return None

        habit = default_habit_data(habit_id, name)
        person[KEY_HABITS].append(habit)
        _LOGGER.debug(
            "Habit '%s' added successfully for person '%s'", habit_id, person_key
        )
        return habit

    def remove_habit(self, person_key: str, habit_id: str) -> bool:
        """Remove a habit from a person."""
        _LOGGER.debug(
            "remove_habit called for person='%s', habit_id='%s'", person_key, habit_id
        )
        person = self.get_person_data(person_key)
        if not person:
            return False

        habits = person.get(KEY_HABITS, [])
        for i, habit in enumerate(habits):
            if habit["id"] == habit_id:
                person[KEY_HABITS].pop(i)
                _LOGGER.debug("Habit '%s' removed successfully", habit_id)
                return True
        _LOGGER.warning("Habit '%s' not found for removal", habit_id)
        return False

    def set_completion(
        self, person_key: str, habit_id: str, date_str: str, completed: bool
    ) -> bool:
        """Set completion status for a habit on a specific date."""
        _LOGGER.debug(
            "set_completion called for person='%s', habit_id='%s', date='%s', completed=%s",
            person_key,
            habit_id,
            date_str,
            completed,
        )
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            _LOGGER.error("Habit '%s' not found for person '%s'", habit_id, person_key)
            return False

        completions = habit.setdefault(KEY_COMPLETIONS, {})
        old_value = completions.get(date_str)
        completions[date_str] = completed

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
        _LOGGER.debug(
            "get_completion called for person='%s', habit_id='%s', date='%s'",
            person_key,
            habit_id,
            date_str,
        )
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            return None
        result = habit.get(KEY_COMPLETIONS, {}).get(date_str)
        _LOGGER.debug("get_completion returning: %s", result)
        return result

    def get_total_completed(self, person_key: str, habit_id: str) -> int:
        """Get total number of days a habit has been completed."""
        _LOGGER.debug(
            "get_total_completed called for person='%s', habit_id='%s'",
            person_key,
            habit_id,
        )
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            return 0
        completions = habit.get(KEY_COMPLETIONS, {})
        total = sum(1 for v in completions.values() if v)
        _LOGGER.debug(
            "get_total_completed returning: %d (from %d total entries)",
            total,
            len(completions),
        )
        return total

    def get_completion_rate(self, person_key: str, habit_id: str) -> float:
        """Get completion rate as a percentage (0-100)."""
        _LOGGER.debug(
            "get_completion_rate called for person='%s', habit_id='%s'",
            person_key,
            habit_id,
        )
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            return 0.0

        completions = habit.get(KEY_COMPLETIONS, {})
        _LOGGER.debug(
            "get_completion_rate: completions dict has %d entries", len(completions)
        )
        if not completions:
            return 0.0

        completed_count = sum(1 for v in completions.values() if v)
        total_days = len(completions)
        rate = round((completed_count / total_days) * 100, 1)
        _LOGGER.debug(
            "get_completion_rate returning: %.1f%% (%d/%d)",
            rate,
            completed_count,
            total_days,
        )
        return rate

    def get_week_completions(self, person_key: str, habit_id: str) -> dict[str, bool]:
        """Get completion status for a habit for the current week."""
        _LOGGER.debug(
            "get_week_completions called for person='%s', habit_id='%s'",
            person_key,
            habit_id,
        )
        week_dates = get_current_week_dates()
        habit = self.get_habit(person_key, habit_id)
        if not habit:
            result = {d: False for d in week_dates}
            _LOGGER.debug(
                "get_week_completions returning default (habit not found): %s",
                result,
            )
            return result

        completions = habit.get(KEY_COMPLETIONS, {})
        result = {d: completions.get(d, False) for d in week_dates}
        _LOGGER.debug("get_week_completions returning: %s", result)
        return result

    def reset_week(self, person_key: str) -> int:
        """Reset all habits for the current week (uncheck all)."""
        _LOGGER.debug("reset_week called for person='%s'", person_key)
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
                    _LOGGER.debug(
                        "Reset completion for habit '%s' on %s", habit["name"], date_str
                    )

        _LOGGER.info("Reset %s completions for person '%s'", reset_count, person_key)
        return reset_count

    def get_person_habits(self, person_key: str) -> list[dict]:
        """Get all habits for a person."""
        _LOGGER.debug("get_person_habits called for '%s'", person_key)
        person = self.get_person_data(person_key)
        if not person:
            return []
        result = person.get(KEY_HABITS, [])
        _LOGGER.debug(
            "get_person_habits returning %d habits: %s",
            len(result),
            [h["name"] for h in result],
        )
        return result

    def get_all_habits(self) -> dict[str, list[dict]]:
        """Get all habits for all people."""
        _LOGGER.debug("get_all_habits called")
        result = {}
        for key in self.person_keys:
            result[key] = self.get_person_habits(key)
        _LOGGER.debug(
            "get_all_habits returning: %s",
            {k: [h["name"] for h in v] for k, v in result.items()},
        )
        return result
