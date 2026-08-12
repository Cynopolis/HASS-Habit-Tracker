"""Config flow for Habit Tracker integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DATA_FILE,
    CONF_NAME,
    DEFAULT_INSTANCE_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_INSTANCE_NAME): str,
        vol.Optional(CONF_DATA_FILE, default=""): str,
    }
)

STEP_HABIT_SCHEMA = vol.Schema(
    {
        vol.Required("habit_id"): str,
        vol.Required("habit_name"): str,
    }
)


class HabitTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Habit Tracker."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_options_flow(cls, config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return HabitTrackerOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a user-initiated config flow."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_SCHEMA,
            )

        # Check for duplicate names
        self._async_abort_entries_match(
            {CONF_NAME: user_input.get(CONF_NAME, DEFAULT_INSTANCE_NAME)}
        )

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
        self._habits_list: list[dict[str, str]] = []
        self._current_step: str = "habits"  # "habits", "add_habit", "remove_habit"

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Main options screen — show list of habits."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add":
                return await self.async_step_add_habit()
            elif action == "remove":
                return await self.async_step_remove_habit()

        # Load current habits from data file
        self._habits_list = self._get_current_habits()

        schema = vol.Schema(
            {
                vol.Required("action", default="add"): vol.In(
                    {"add": "Add Habit", "remove": "Remove Habit"}
                ),
            }
        )

        # Build display text for current habits
        if self._habits_list:
            habit_names = "\n".join(
                f"• {h['name']} ({h['id']})" for h in self._habits_list
            )
            description = f"**Current habits:**\n{habit_names}"
        else:
            description = "No habits configured yet."

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_text=description,
        )

    async def async_step_add_habit(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new habit."""
        if user_input is None:
            return self.async_show_form(
                step_id="add_habit",
                data_schema=STEP_HABIT_SCHEMA,
            )

        habit_id = user_input["habit_id"].strip().lower().replace(" ", "_")
        habit_name = user_input["habit_name"].strip()

        if not habit_id or not habit_name:
            return self.async_show_form(
                step_id="add_habit",
                data_schema=STEP_HABIT_SCHEMA,
                errors={"base": "habits_cannot_be_empty"},
            )

        # Check for duplicate habit_id
        existing_ids = [h["id"] for h in self._habits_list]
        if habit_id in existing_ids:
            return self.async_show_form(
                step_id="add_habit",
                data_schema=STEP_HABIT_SCHEMA,
                errors={"habit_id": "already_exists"},
            )

        # Save to options
        new_habits = self._habits_list + [{"id": habit_id, "name": habit_name}]
        self._update_options(habits=new_habits)

        return self.async_create_entry(data={})

    async def async_step_remove_habit(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Remove an existing habit."""
        if user_input is None:
            if not self._habits_list:
                return self.async_abort(reason="no_habits_to_remove")

            schema = vol.Schema(
                {
                    vol.Required("habit_id"): vol.In(
                        {h["id"]: h["name"] for h in self._habits_list}
                    ),
                }
            )
            return self.async_show_form(
                step_id="remove_habit",
                data_schema=schema,
            )

        habit_id = user_input["habit_id"]
        remaining = [h for h in self._habits_list if h["id"] != habit_id]
        self._update_options(habits=remaining)

        return self.async_create_entry(data={})

    def _get_current_habits(self) -> list[dict[str, str]]:
        """Load configured habits from options."""
        return self.config_entry.options.get("habits", [])

    def _update_options(self, habits: list[dict[str, str]]) -> None:
        """Update config entry options with new habit list."""
        updated = dict(self.config_entry.options)
        updated["habits"] = habits
        self.hass.config_entries.async_update_entry(self.config_entry, options=updated)
