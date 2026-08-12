"""The Habit Tracker integration."""

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import STORAGE_DIR

from .const import (
    ATTR_COMPLETED,
    ATTR_DATE,
    ATTR_HABIT_ID,
    ATTR_HABIT_NAME,
    CONF_DATA_FILE,
    CONF_NAME,
    DEFAULT_INSTANCE_NAME,
    DOMAIN,
    SERVICE_ADD_HABIT,
    SERVICE_REMOVE_HABIT,
    SERVICE_RESET_WEEK,
    SERVICE_SET_COMPLETION,
)
from .data_manager import DataManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["button", "binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Habit Tracker component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Habit Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    name = entry.options.get(CONF_NAME, DEFAULT_INSTANCE_NAME)
    data_file_name = entry.options.get(
        CONF_DATA_FILE, f"habit_tracker_{entry.entry_id}.json"
    )

    # Build path to data file in HA's storage directory
    data_file = Path(hass.config.path(STORAGE_DIR)) / data_file_name

    # Create data manager
    data_manager = DataManager(hass, data_file)

    # Add person if not exists
    person_key = entry.entry_id
    data_manager.add_person(person_key, name)

    # Register services
    _async_register_services(hass, entry)

    # Store in hass.data for access from platforms and services
    hass.data[DOMAIN][entry.entry_id] = {
        "data_manager": data_manager,
        "person_key": person_key,
        "name": name,
    }

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _async_register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register integration services."""
    domain = DOMAIN
    entry_id = entry.entry_id

    async def handle_add_habit(service_call):
        """Handle add_habit service call."""
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        habit_id = (
            service_call.data.get(ATTR_HABIT_ID, "").strip().lower().replace(" ", "_")
        )
        habit_name = service_call.data.get(ATTR_HABIT_NAME, "").strip()

        if not habit_id or not habit_name:
            _LOGGER.warning(
                "Both habit_id and habit_name are required for %s", SERVICE_ADD_HABIT
            )
            return

        habit = dm.add_habit(person_key, habit_id, habit_name)
        if habit:
            await hass.config_entries.async_forward_entry_setups(
                entry, ["binary_sensor", "sensor"]
            )
            _LOGGER.info("Habit '%s' added via service", habit_name)

    async def handle_remove_habit(service_call):
        """Handle remove_habit service call."""
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        habit_id = (
            service_call.data.get(ATTR_HABIT_ID, "").strip().lower().replace(" ", "_")
        )
        if not habit_id:
            _LOGGER.warning("habit_id is required for %s", SERVICE_REMOVE_HABIT)
            return

        dm.remove_habit(person_key, habit_id)
        # Reload to remove entities
        await hass.config_entries.async_reload(entry.entry_id)

    async def handle_set_completion(service_call):
        """Handle set_completion service call."""
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        habit_id = (
            service_call.data.get(ATTR_HABIT_ID, "").strip().lower().replace(" ", "_")
        )
        date_str = service_call.data.get(ATTR_DATE, "")
        completed = service_call.data.get(ATTR_COMPLETED, True)

        if not habit_id or not date_str:
            _LOGGER.warning(
                "habit_id and date are required for %s", SERVICE_SET_COMPLETION
            )
            return

        dm.set_completion(person_key, habit_id, date_str, completed)

    async def handle_reset_week(service_call):
        """Handle reset_week service call."""
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        count = dm.reset_week(person_key)
        _LOGGER.info("Week reset for %s, cleared %s completions", entry_id, count)

    # Register services with entity_id context
    hass.services.async_register(
        domain,
        SERVICE_ADD_HABIT,
        handle_add_habit,
    )
    hass.services.async_register(
        domain,
        SERVICE_REMOVE_HABIT,
        handle_remove_habit,
    )
    hass.services.async_register(
        domain,
        SERVICE_SET_COMPLETION,
        handle_set_completion,
    )
    hass.services.async_register(
        domain,
        SERVICE_RESET_WEEK,
        handle_reset_week,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove a config entry."""
    # Clean up data file
    data_file_name = entry.options.get(
        CONF_DATA_FILE, f"habit_tracker_{entry.entry_id}.json"
    )
    data_file = Path(hass.config.path(STORAGE_DIR)) / data_file_name

    if data_file.exists():
        try:
            data_file.unlink()
            _LOGGER.info("Removed data file: %s", data_file)
        except IOError as e:
            _LOGGER.error("Failed to remove data file: %s", e)

    return True
