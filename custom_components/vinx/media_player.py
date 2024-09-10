import logging

from bidict import bidict
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState
from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.vinx import LW3, DeviceInformation, VinxRuntimeData
from custom_components.vinx.lw3 import NodeResponse, is_encoder_discovery_node

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


class AbstractVinxMediaPlayerEntity(MediaPlayerEntity):
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
        # Use increasingly less descriptive names depending on what information is available
        device_label = self._device_information.device_label
        serial_number = self._device_information.device_info.get("serial_number")

        if device_label:
            return f"{self._device_information.device_label} media player"
        elif serial_number:
            return f"VINX {serial_number} media player"
        else:
            return "VINX media player"


class VinxEncoder(AbstractVinxMediaPlayerEntity):
    pass


class VinxDecoder(AbstractVinxMediaPlayerEntity):
    def __init__(self, lw3: LW3, device_information: DeviceInformation) -> None:
        super().__init__(lw3, device_information)
        self._source = None
        self._source_list = None
        self._source_bidict = bidict()

    _attr_supported_features = MediaPlayerEntityFeature.SELECT_SOURCE

    async def async_update(self):
        # Populate the source list only once. Sort it alphabetically, since the order of discovered devices
        # may differ from device to device.
        if self._source_list is None:
            await self.populate_source_bidict()
            self._source_list = sorted(list(self._source_bidict.values()))
            _LOGGER.info(f"{self.name} source list populated with {len(self._source_list)} sources")

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def source_list(self) -> list[str] | None:
        return self._source_list

    async def populate_source_bidict(self):
        """Queries the device for discovered devices, filters out everything that isn't a VINX encoder,
        then builds a bidict mapping between the device label and video channel ID."""
        async with self._lw3.connection():
            discovery_nodes = await self._lw3.get_all("/DISCOVERY")
            encoder_nodes: list[NodeResponse] = list(filter(is_encoder_discovery_node, discovery_nodes))

            for encoder_node in encoder_nodes:
                device_name = await self._lw3.get_property(f"{encoder_node.path}.DeviceName")
                video_channel_id = await self._lw3.get_property(f"{encoder_node.path}.VideoChannelId")
                self._source_bidict.put(str(video_channel_id), str(device_name))
