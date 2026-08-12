"""Config flow for Habit Tracker integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_DATA_FILE,
    CONF_NAME,
    DEFAULT_INSTANCE_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_INSTANCE_NAME): str,
        vol.Optional(CONF_DATA_FILE, default=""): str,
    }
)


class HabitTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Habit Tracker."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HabitTrackerOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a step initiated by the user."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        # Check if already configured
        self._async_abort_entries_match({
            CONF_NAME: user_input.get(CONF_NAME, DEFAULT_INSTANCE_NAME),
        })

        return self.async_create_entry(
            title=user_input[CONF_NAME],
            data={},
            options=user_input,
        )


class HabitTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Habit Tracker."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = {
            vol.Required(
                CONF_NAME,
                default=self.config_entry.options.get(CONF_NAME, DEFAULT_INSTANCE_NAME),
            ): str,
            vol.Optional(
                CONF_DATA_FILE,
                default=self.config_entry.options.get(
                    CONF_DATA_FILE, f"habit_tracker_{self.config_entry.entry_id}.json"
                ),
            ): str,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )


@callback
def async_get_available_entries(hass) -> list[tuple[str, str]]:
    """Get all configured habit tracker instances.
    
    Returns list of (entry_id, name) tuples.
    """
    entries = hass.config_entries.async_entries(DOMAIN)
    return [(entry.entry_id, entry.options.get(CONF_NAME, DEFAULT_INSTANCE_NAME)) for entry in entries]
