"""Config flow for Breaking Changes integration."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_NAME


class BreakingChangesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Breaking Changes."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            # Nessuna opzione: solo conferma
            return self.async_show_form(step_id="user", data_schema=None)

        return self.async_create_entry(title=DEFAULT_NAME, data={})
