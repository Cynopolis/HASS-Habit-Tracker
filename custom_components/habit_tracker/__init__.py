"""The Habit Tracker integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    ATTR_COMPLETED,
    ATTR_DATE,
    ATTR_HABIT_ID,
    ATTR_HABIT_NAME,
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

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Habit Tracker component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Habit Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    name = entry.options.get(CONF_NAME, DEFAULT_INSTANCE_NAME)

    # Create data manager using HA's Store helper
    data_manager = DataManager(hass)

    # Load existing data asynchronously
    await data_manager.async_load()

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

        dm.add_habit(person_key, habit_id, habit_name)
        await dm.async_save()

        # Reload platforms to create new entities
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
        await dm.async_save()

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
        await dm.async_save()

    async def handle_reset_week(service_call):
        """Handle reset_week service call."""
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        count = dm.reset_week(person_key)
        await dm.async_save()
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
    # Data is managed by HA's Store helper — no manual cleanup needed
    _LOGGER.info("Removed habit tracker entry for '%s'", entry.title)
    return True
