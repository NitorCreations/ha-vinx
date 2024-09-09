from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_HOST, CONF_PORT, DOMAIN
from .lw3 import LW3

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=6107): int,
    }
)


class VinxConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle user initiated configuration"""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Try to connect to the device
                lw3_device = LW3(user_input["host"], user_input["port"])
                await lw3_device.connect()

                # Make a title for the entry
                title = str(await lw3_device.get_property("/.ProductName"))

                # Disconnect, this was just for validation
                await lw3_device.disconnect()
            except (BrokenPipeError, ConnectionError, OSError):  # all technically OSError
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)
