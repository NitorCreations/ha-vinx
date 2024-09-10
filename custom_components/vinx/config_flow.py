import logging

from typing import Any

import voluptuous as vol

from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.device_registry import format_mac

from .const import CONF_HOST, CONF_PORT, DOMAIN
from .lw3 import LW3

_LOGGER = logging.getLogger(__name__)


class VinxConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        # Potentially prepopulated values (e.g. during auto-discovery)
        self.host: str | None = None
        self.port: int = 6107

    @property
    def schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=self.host): str,
                vol.Required(CONF_PORT, default=self.port): int,
            }
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle user initiated configuration"""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Verify that the device is connectable
                lw3 = LW3(user_input["host"], user_input["port"])
                async with lw3.connection():
                    # Query information for the entry title and entry unique ID
                    product_name = await lw3.get_property("/.ProductName")
                    device_label = await lw3.get_property("/SYS/MB.DeviceLabel")
                    mac_address = await lw3.get_property("/.MacAddress")

                    title = f"{device_label} ({product_name})"

                    unique_id = format_mac(str(mac_address))
                    await self.async_set_unique_id(unique_id)

                    # Abort the configuration if the device is already configured
                    self._abort_if_unique_id_configured()
            except (BrokenPipeError, ConnectionError, OSError):  # all technically OSError
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(step_id="user", data_schema=self.schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        _LOGGER.info(f"Zeroconf discovery info: {discovery_info}")

        # Abort if the device is already configured
        unique_id = format_mac(discovery_info.properties.get("mac"))
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        # Pre-populate the form
        self.host = discovery_info.ip_address
        self.port = discovery_info.port

        # Trigger the user configuration flow
        return await self.async_step_user()
