"""Button platform for Habit Tracker - provides add_habit button."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ICON_CHART,
    SUFFIX_BUTTON_ADD,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Habit Tracker button platform."""
    _LOGGER.debug("async_setup_entry called for button platform")
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_manager = data["data_manager"]
    person_key = data["person_key"]
    name = data["name"]
    _LOGGER.debug("Person key: %s, Name: %s", person_key, name)

    # Add habit button
    _LOGGER.debug("Creating add habit button")
    add_button = HabitTrackerAddButton(
        data_manager=data_manager,
        person_key=person_key,
        config_entry=config_entry,
        name=name,
    )
    async_add_entities([add_button])
    _LOGGER.debug("Adding 1 button to HA")


class HabitTrackerAddButton(ButtonEntity):
    """Represents the 'Add Habit' button for a person's tracker."""

    _attr_name = None  # Use device name + clean entity_id
    _attr_icon = ICON_CHART

    def __init__(
        self,
        data_manager,
        person_key: str,
        config_entry,
        name: str,
    ) -> None:
        """Initialize the add habit button."""
        self._data_manager = data_manager
        self._person_key = person_key
        self._config_entry = config_entry
        self._instance_name = name

        self._attr_unique_id = f"{person_key}_{SUFFIX_BUTTON_ADD}"
        self.entity_id = f"button.{person_key}_add_habit"
        _LOGGER.debug(
            "Entity ID: %s, Unique ID: %s", self.entity_id, self._attr_unique_id
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, person_key)},
            name=f"Habit Tracker - {name}",
            manufacturer="Custom",
            model="Habit Tracker",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    async def async_press(self) -> None:
        """Press the button - triggers UI to add a habit."""
        _LOGGER.debug("async_press called for add habit button")
        # The button press is informational; actual habit addition
        # is done via service call. We show a message.
        self.hass.bus.async_fire(
            f"{DOMAIN}_add_habit_requested",
            {
                "person_key": self._person_key,
                "instance_name": self._instance_name,
            },
        )
        _LOGGER.debug("Bus event fired: %s_add_habit_requested", DOMAIN)
