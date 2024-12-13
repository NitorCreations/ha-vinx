import logging

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import UndefinedType

from custom_components.vinx import LW3, DeviceInformation, DeviceType, VinxRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    # Extract stored runtime data
    runtime_data: VinxRuntimeData = entry.runtime_data
    _LOGGER.info(f"Runtime data: {runtime_data}")

    # Add entity to Home Assistant
    if runtime_data.device_information.get_device_type() == DeviceType.ENCODER:
        async_add_entities([VinxPreviewImageEntity(hass, runtime_data.lw3, runtime_data.device_information)])
    else:
        _LOGGER.info(f"Device type is not {DeviceType.ENCODER}, not adding image entity")


class VinxPreviewImageEntity(ImageEntity):
    def __init__(self, hass: HomeAssistant, lw3: LW3, device_information: DeviceInformation) -> None:
        super().__init__(hass)

        self._lw3 = lw3
        self._device_information = device_information

    @property
    def unique_id(self) -> str | None:
        mac_address = self._device_information.mac_address

        return f"vinx_{mac_address}_preview_image"

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_information.device_info

    @property
    def name(self):
        # Use increasingly less descriptive names depending on what information is available
        device_label = self._device_information.device_label
        serial_number = self._device_information.device_info.get("serial_number")

        if device_label:
            return f"{self._device_information.device_label} preview image"
        elif serial_number:
            return f"VINX {serial_number} preview image"
        else:
            return "VINX preview image"

    @property
    def image_url(self) -> str | None | UndefinedType:
        return "http://10.110.3.75:8480/capture.jpg"
        # return f"http://{self._device_information.ip_address}/capture.jpg"
