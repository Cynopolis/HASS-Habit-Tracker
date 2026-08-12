"""Sensor platform for Habit Tracker - provides stats per habit."""

import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    ICON_COUNTER,
    ICON_CHECK_CIRCLE,
)
from .data_manager import DataManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Habit Tracker sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_manager: DataManager = data["data_manager"]
    person_key = data["person_key"]
    name = data["name"]

    habits = data_manager.get_person_habits(person_key)
    sensors = []

    for habit in habits:
        # Total completed counter
        total_sensor = HabitTrackerTotalSensor(
            data_manager=data_manager,
            person_key=person_key,
            habit=habit,
            config_entry=config_entry,
            instance_name=name,
        )
        sensors.append(total_sensor)

        # Completion rate sensor
        rate_sensor = HabitTrackerRateSensor(
            data_manager=data_manager,
            person_key=person_key,
            habit=habit,
            config_entry=config_entry,
            instance_name=name,
        )
        sensors.append(rate_sensor)

    async_add_entities(sensors)


class HabitTrackerTotalSensor(SensorEntity):
    """Represents the total number of days a habit has been completed."""

    _attr_has_entity_name = True
    _attr_name = "Total Completed"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = "days"
    _attr_icon = ICON_COUNTER

    def __init__(
        self,
        data_manager: DataManager,
        person_key: str,
        habit: dict,
        config_entry,
        instance_name: str,
    ) -> None:
        """Initialize the total sensor."""
        self._data_manager = data_manager
        self._person_key = person_key
        self._habit = habit
        self._habit_id = habit["id"]
        self._habit_name = habit["name"]
        self._config_entry = config_entry
        self._instance_name = name

        safe_habit_id = self._habit_id.replace("-", "_").replace(" ", "_")
        self._attr_unique_id = f"{person_key}_total_{safe_habit_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, person_key)},
            name=f"Habit Tracker - {instance_name}",
            manufacturer="Custom",
            model="Habit Tracker",
        )

    @property
    def native_value(self) -> int:
        """Return the total number of completed days."""
        return self._data_manager.get_total_completed(
            self._person_key, self._habit_id
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True


class HabitTrackerRateSensor(SensorEntity):
    """Represents the completion rate of a habit as a percentage."""

    _attr_has_entity_name = True
    _attr_name = "Completion Rate"
    _attr_device_class = SensorDeviceClass.PERCENTAGE
    _attr_native_unit_of_measurement = "%"
    _attr_icon = ICON_CHECK_CIRCLE
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        data_manager: DataManager,
        person_key: str,
        habit: dict,
        config_entry,
        instance_name: str,
    ) -> None:
        """Initialize the rate sensor."""
        self._data_manager = data_manager
        self._person_key = person_key
        self._habit = habit
        self._habit_id = habit["id"]
        self._habit_name = habit["name"]
        self._config_entry = config_entry
        self._instance_name = instance_name

        safe_habit_id = self._habit_id.replace("-", "_").replace(" ", "_")
        self._attr_unique_id = f"{person_key}_rate_{safe_habit_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, person_key)},
            name=f"Habit Tracker - {instance_name}",
            manufacturer="Custom",
            model="Habit Tracker",
        )

    @property
    def native_value(self) -> float:
        """Return the completion rate as a percentage."""
        return self._data_manager.get_completion_rate(
            self._person_key, self._habit_id
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True
