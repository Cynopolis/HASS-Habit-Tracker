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
    _LOGGER.debug("Habit Tracker async_setup called with config: %s", config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Habit Tracker from a config entry."""
    _LOGGER.debug("async_setup_entry called for entry %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})

    name = entry.options.get(CONF_NAME, DEFAULT_INSTANCE_NAME)
    _LOGGER.debug("Integration name: %s", name)

    # Create data manager using HA's Store helper
    data_manager = DataManager(hass)
    _LOGGER.debug("DataManager created")

    # Load existing data asynchronously
    await data_manager.async_load()
    _LOGGER.debug("Data loaded from store, person_keys: %s", data_manager.person_keys)

    # Add person if not exists
    person_key = entry.entry_id
    data_manager.add_person(person_key, name)
    _LOGGER.debug("Person '%s' registered with key '%s'", name, person_key)

    # Register services
    _async_register_services(hass, entry)
    _LOGGER.debug("Services registered for entry %s", entry.entry_id)

    # Store in hass.data for access from platforms and services
    hass.data[DOMAIN][entry.entry_id] = {
        "data_manager": data_manager,
        "person_key": person_key,
        "name": name,
    }

    # Forward setup to platforms
    _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("All platforms set up successfully")

    return True


def _async_register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register integration services."""
    domain = DOMAIN
    entry_id = entry.entry_id

    async def handle_add_habit(service_call):
        """Handle add_habit service call."""
        _LOGGER.debug("handle_add_habit called with data: %s", service_call.data)
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        habit_id = (
            service_call.data.get(ATTR_HABIT_ID, "").strip().lower().replace(" ", "_")
        )
        habit_name = service_call.data.get(ATTR_HABIT_NAME, "").strip()
        _LOGGER.debug("Parsed habit_id='%s', habit_name='%s'", habit_id, habit_name)

        if not habit_id or not habit_name:
            _LOGGER.warning(
                "Both habit_id and habit_name are required for %s", SERVICE_ADD_HABIT
            )
            return

        result = dm.add_habit(person_key, habit_id, habit_name)
        _LOGGER.debug("add_habit result: %s", result)
        await dm.async_save()
        _LOGGER.debug("Data saved after add_habit")

        # Reload platforms to create new entities
        _LOGGER.debug("Reloading platforms for binary_sensor and sensor")
        await hass.config_entries.async_forward_entry_setups(
            entry, ["binary_sensor", "sensor"]
        )
        _LOGGER.info("Habit '%s' added via service", habit_name)

    async def handle_remove_habit(service_call):
        """Handle remove_habit service call."""
        _LOGGER.debug("handle_remove_habit called with data: %s", service_call.data)
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        habit_id = (
            service_call.data.get(ATTR_HABIT_ID, "").strip().lower().replace(" ", "_")
        )
        _LOGGER.debug("Parsed habit_id='%s'", habit_id)
        if not habit_id:
            _LOGGER.warning("habit_id is required for %s", SERVICE_REMOVE_HABIT)
            return

        result = dm.remove_habit(person_key, habit_id)
        _LOGGER.debug("remove_habit result: %s", result)
        await dm.async_save()
        _LOGGER.debug("Data saved after remove_habit")

        # Reload to remove entities
        _LOGGER.debug("Reloading entry %s", entry.entry_id)
        await hass.config_entries.async_reload(entry.entry_id)

    async def handle_set_completion(service_call):
        """Handle set_completion service call."""
        _LOGGER.debug("handle_set_completion called with data: %s", service_call.data)
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        habit_id = (
            service_call.data.get(ATTR_HABIT_ID, "").strip().lower().replace(" ", "_")
        )
        date_str = service_call.data.get(ATTR_DATE, "")
        completed = service_call.data.get(ATTR_COMPLETED, True)
        _LOGGER.debug(
            "Parsed habit_id='%s', date_str='%s', completed=%s",
            habit_id,
            date_str,
            completed,
        )

        if not habit_id or not date_str:
            _LOGGER.warning(
                "habit_id and date are required for %s", SERVICE_SET_COMPLETION
            )
            return

        result = dm.set_completion(person_key, habit_id, date_str, completed)
        _LOGGER.debug("set_completion result: %s", result)
        await dm.async_save()
        _LOGGER.debug("Data saved after set_completion")

    async def handle_reset_week(service_call):
        """Handle reset_week service call."""
        _LOGGER.debug("handle_reset_week called")
        data = hass.data[domain][entry_id]
        dm = data["data_manager"]
        person_key = data["person_key"]

        count = dm.reset_week(person_key)
        _LOGGER.debug("reset_week returned count=%s", count)
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
    _LOGGER.debug("async_unload_entry called for entry %s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    _LOGGER.debug("unload_platforms result: %s", unload_ok)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug("Removed entry from hass.data")

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove a config entry."""
    # Data is managed by HA's Store helper — no manual cleanup needed
    _LOGGER.info("Removed habit tracker entry for '%s'", entry.title)
    return True
