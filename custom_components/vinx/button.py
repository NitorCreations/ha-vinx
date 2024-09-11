import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.vinx import LW3, DeviceInformation, VinxRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    # Extract stored runtime data
    runtime_data: VinxRuntimeData = entry.runtime_data
    _LOGGER.info(f"Runtime data: {runtime_data}")

    # Add entity to Home Assistant
    async_add_entities([VinxRebootButtonEntity(runtime_data.lw3, runtime_data.device_information)])


class VinxRebootButtonEntity(ButtonEntity):
    def __init__(self, lw3: LW3, device_information: DeviceInformation) -> None:
        self._lw3 = lw3
        self._device_information = device_information

    _attr_device_class = ButtonDeviceClass.RESTART

    @property
    def unique_id(self) -> str | None:
        return f"vinx_{self._device_information.mac_address}_reboot_button"

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_information.device_info

    @property
    def name(self):
        # Use increasingly less descriptive names depending on what information is available
        device_label = self._device_information.device_label
        serial_number = self._device_information.device_info.get("serial_number")

        if device_label:
            return f"{self._device_information.device_label} reboot button"
        elif serial_number:
            return f"VINX {serial_number} reboot button"
        else:
            return "VINX reboot button"

    async def async_press(self) -> None:
        async with self._lw3.connection():
            _LOGGER.info("Issuing device reset")
            await self._lw3.call("/SYS", "reset(1)")
