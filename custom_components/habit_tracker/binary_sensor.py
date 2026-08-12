"""Binary sensor platform for Habit Tracker - represents habit completion per day."""

import logging
from datetime import date, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DAYS_OF_WEEK,
    DOMAIN,
    ICON_HABIT,
    ICON_HABIT_EMPTY,
    KEY_COMPLETIONS,
    SUFFIX_BINARY_SENSOR,
)
from .data_manager import DataManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Habit Tracker binary sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_manager: DataManager = data["data_manager"]
    person_key = data["person_key"]
    name = data["name"]

    # Read habits from config options
    habits = config_entry.options.get("habits", [])
    sensors = []

    for habit in habits:
        sensor = HabitTrackerBinarySensor(
            data_manager=data_manager,
            person_key=person_key,
            habit=habit,
            config_entry=config_entry,
            instance_name=name,
        )
        sensors.append(sensor)

    async_add_entities(sensors)


class HabitTrackerBinarySensor(BinarySensorEntity):
    """Represents the completion status of a habit for the current week."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        data_manager: DataManager,
        person_key: str,
        habit: dict,
        config_entry,
        instance_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        self._data_manager = data_manager
        self._person_key = person_key
        self._habit = habit
        self._habit_id = habit["id"]
        self._habit_name = habit["name"]
        self._config_entry = config_entry
        self._instance_name = instance_name

        # Entity identification
        safe_habit_id = self._habit_id.replace("-", "_").replace(" ", "_")
        self._attr_unique_id = f"{person_key}_{SUFFIX_BINARY_SENSOR}_{safe_habit_id}"
        self._attr_name = self._habit_name

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, person_key)},
            name=f"Habit Tracker - {instance_name}",
            manufacturer="Custom",
            model="Habit Tracker",
        )

        # State tracking for current week
        self._week_dates = []
        self._current_day_index = 0
        self._update_week()

    def _update_week(self) -> None:
        """Update the current week's dates."""
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        self._week_dates = [(monday + timedelta(days=i)).isoformat() for i in range(7)]
        self._current_day_index = today.weekday()

    @property
    def is_on(self) -> bool:
        """Return True if the habit was completed on the current day."""
        self._update_week()
        current_date = self._week_dates[self._current_day_index]
        completions = self._habit.get(KEY_COMPLETIONS, {})
        return bool(completions.get(current_date))

    @property
    def extra_state_attributes(self) -> dict:
        """Return state attributes for the weekly grid view."""
        self._update_week()
        completions = self._habit.get(KEY_COMPLETIONS, {})

        # Build week grid data
        week_grid = {}
        for i, date_str in enumerate(self._week_dates):
            day_name = DAYS_OF_WEEK[i]
            is_today = i == self._current_day_index
            week_grid[day_name] = {
                "date": date_str,
                "completed": bool(completions.get(date_str)),
                "is_today": is_today,
            }

        total_completed = sum(1 for v in completions.values() if v)
        total_days = len(completions)
        rate = round((total_completed / total_days * 100), 1) if total_days > 0 else 0.0

        return {
            "habit_id": self._habit_id,
            "person_key": self._person_key,
            "week_grid": week_grid,
            "total_completed": total_completed,
            "completion_rate": rate,
            "current_day_index": self._current_day_index,
        }

    @property
    def icon(self) -> str:
        """Return the icon based on current day completion."""
        return ICON_HABIT if self.is_on else ICON_HABIT_EMPTY

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    async def async_turn_on(self, **kwargs) -> None:
        """Mark the habit as completed for today."""
        self._update_week()
        current_date = self._week_dates[self._current_day_index]
        self._data_manager.set_completion(
            self._person_key, self._habit_id, current_date, True
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Mark the habit as not completed for today."""
        self._update_week()
        current_date = self._week_dates[self._current_day_index]
        self._data_manager.set_completion(
            self._person_key, self._habit_id, current_date, False
        )
        self.async_write_ha_state()
