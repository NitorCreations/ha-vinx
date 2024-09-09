import logging

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState
from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.vinx import LW3, DeviceInformation, VinxRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    # Extract stored runtime data
    runtime_data: VinxRuntimeData = entry.runtime_data
    _LOGGER.info(f"Runtime data: {runtime_data}")

    # Add entity to Home Assistant
    product_name = runtime_data.device_information.product_name
    if product_name.endswith("ENC"):
        async_add_entities([VinxEncoder(runtime_data.lw3, runtime_data.device_information)])
        pass
    elif product_name.endswith("DEC"):
        async_add_entities([VinxDecoder(runtime_data.lw3, runtime_data.device_information)])
        pass
    else:
        _LOGGER.warning("Unknown device type, no entities will be added")


class AbstractVinxDevice(MediaPlayerEntity):
    def __init__(self, lw3: LW3, device_information: DeviceInformation) -> None:
        self._lw3 = lw3
        self._device_information = device_information

        self._device_class = "receiver"
        self._state = MediaPlayerState.IDLE

    @property
    def device_class(self):
        return self._device_class

    @property
    def unique_id(self) -> str | None:
        mac_address = self._device_information.mac_address

        return f"vinx_{mac_address}_media_player"

    @property
    def state(self):
        return self._state

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_information.device_info

    @property
    def name(self):
        return "Media Player"


class VinxEncoder(AbstractVinxDevice):
    pass


class VinxDecoder(AbstractVinxDevice):
    def __init__(self, lw3: LW3, device_information: DeviceInformation) -> None:
        super().__init__(lw3, device_information)

        _attr_supported_features = MediaPlayerEntityFeature.SELECT_SOURCE
