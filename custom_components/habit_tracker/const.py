"""Constants for the Habit Tracker integration."""

from datetime import date, timedelta
from typing import Final

DOMAIN: Final = "habit_tracker"

# Default name for a new habit tracker instance
DEFAULT_INSTANCE_NAME: Final = "Habit Tracker"

# Days of the week for the grid display
DAYS_OF_WEEK: Final = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYS_OF_WEEK_FULL: Final = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Config entry keys
CONF_NAME: Final = "name"
CONF_HABITS: Final = "habits"
CONF_DATA_FILE: Final = "data_file"

# Entity suffixes
SUFFIX_BUTTON_ADD: Final = "add_habit"
SUFFIX_BINARY_SENSOR: Final = "habit"
SUFFIX_SENSOR_TOTAL: Final = "total_completed"
SUFFIX_SENSOR_RATE: Final = "completion_rate"

# State values
STATE_COMPLETED: Final = "completed"
STATE_NOT_COMPLETED: Final = "not_completed"

# Data storage keys
KEY_PEOPLE: Final = "people"
KEY_HABITS: Final = "habits"
KEY_NAME: Final = "name"
KEY_COMPLETIONS: Final = "completions"  # dict of date -> habit_id -> bool

# Service definitions
SERVICE_ADD_HABIT: Final = "add_habit"
SERVICE_REMOVE_HABIT: Final = "remove_habit"
SERVICE_SET_COMPLETION: Final = "set_completion"
SERVICE_RESET_WEEK: Final = "reset_week"

# Service schemas
ATTR_HABIT_ID: Final = "habit_id"
ATTR_HABIT_NAME: Final = "habit_name"
ATTR_DATE: Final = "date"
ATTR_COMPLETED: Final = "completed"
ATTR_PERSON_KEY: Final = "person_key"

# Icon definitions
ICON_HABIT: Final = "mdi:checkbox-marked-circle-outline"
ICON_HABIT_EMPTY: Final = "mdi:checkbox-blank-circle-outline"
ICON_CHART: Final = "mdi:chart-line"
ICON_CHECK_CIRCLE: Final = "mdi:check-circle"
ICON_COUNTER: Final = "mdi:counter"


# Default data structure for a person's habits
def default_person_data() -> dict:
    """Return default data structure for a person."""
    return {
        KEY_NAME: "",
        KEY_HABITS: [],  # List of habit dicts
    }


def default_habit_data(habit_id: str, name: str) -> dict:
    """Return default data structure for a habit."""
    return {
        "id": habit_id,
        "name": name,
        KEY_COMPLETIONS: {},  # date_string -> bool
    }


def get_current_week_dates() -> list[str]:
    """Return list of date strings for the current week (Mon-Sun)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return [(monday + timedelta(days=i)).isoformat() for i in range(7)]


def get_habit_entity_id(person_key: str, habit_id: str) -> str:
    """Generate entity ID for a habit binary sensor."""
    return f"binary_sensor.habit_tracker_{person_key}_{habit_id}"


def get_total_completed_entity_id(person_key: str, habit_id: str) -> str:
    """Generate entity ID for total completed counter."""
    return f"sensor.habit_tracker_{person_key}_{habit_id}_total"


def get_completion_rate_entity_id(person_key: str, habit_id: str) -> str:
    """Generate entity ID for completion rate sensor."""
    return f"sensor.habit_tracker_{person_key}_{habit_id}_rate"
