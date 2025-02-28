import asyncio
import logging

from bidict import bidict
from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import Event
from pylw3 import LW3, NodeResponse, is_encoder_discovery_node

from custom_components.vinx import DeviceInformation, DeviceType, VinxEntity, VinxRuntimeData
from custom_components.vinx.const import EVENT_DISCOVER_SOURCES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(_hass, entry, async_add_entities):
    # Extract stored runtime data
    runtime_data: VinxRuntimeData = entry.runtime_data
    _LOGGER.info(f"Runtime data: {runtime_data}")

    # Add entity to Home Assistant
    device_type = runtime_data.device_information.get_device_type()
    if device_type == DeviceType.ENCODER:
        async_add_entities([VinxEncoder(runtime_data.lw3, runtime_data.device_information)])
        pass
    elif device_type == DeviceType.DECODER:
        async_add_entities([VinxDecoder(runtime_data.lw3, runtime_data.device_information)])
        pass
    else:
        _LOGGER.warning("Unknown device type, no entities will be added")


class AbstractVinxMediaPlayerEntity(VinxEntity, MediaPlayerEntity):
    def __init__(self, lw3: LW3, device_information: DeviceInformation) -> None:
        super().__init__(device_information, "media player", "media_player")
        self._lw3 = lw3

        self._state = MediaPlayerState.IDLE

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    @property
    def state(self) -> MediaPlayerState:
        return self._state


class VinxEncoder(AbstractVinxMediaPlayerEntity):
    async def async_update(self):
        async with self._lw3.connection():
            # Query signal status
            signal_present = await self._lw3.get_property("/MEDIA/VIDEO/I1.SignalPresent")
            self._state = MediaPlayerState.PLAYING if str(signal_present) == "1" else MediaPlayerState.IDLE


class VinxDecoder(AbstractVinxMediaPlayerEntity):
    def __init__(self, lw3: LW3, device_information: DeviceInformation) -> None:
        super().__init__(lw3, device_information)
        self._source = None
        self._source_bidict = bidict()
        self._update_sources_lock = asyncio.Lock()

    _attr_supported_features = MediaPlayerEntityFeature.SELECT_SOURCE

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def source_list(self) -> list[str] | None:
        # Sort the list alphabetically, since the order of discovered devices may differ from device to device.
        return sorted(list(self._source_bidict.values()))

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        # Re-populate the source list when EVENT_DISCOVER_DEVICES is fired
        self.async_on_remove(self.hass.bus.async_listen(EVENT_DISCOVER_SOURCES, self.handle_discover_sources_event))

    async def async_update(self):
        # Populate the source list if its empty
        if len(self._source_bidict.items()) == 0:
            await self.populate_source_bidict()

        async with self._lw3.connection():
            # Query current source
            video_channel_id = await self._lw3.get_property("/SYS/MB/PHY.VideoChannelId")
            self._source = str(self._source_bidict.get(str(video_channel_id)))

            # Query signal status
            signal_present = await self._lw3.get_property("/MEDIA/VIDEO/I1.SignalPresent")
            self._state = MediaPlayerState.PLAYING if str(signal_present) == "1" else MediaPlayerState.IDLE

    async def async_select_source(self, source: str) -> None:
        self._source = source
        video_channel_id = self._source_bidict.inverse.get(source)

        async with self._lw3.connection():
            await self._lw3.set_property("/SYS/MB/PHY.VideoChannelId", video_channel_id)

    async def handle_discover_sources_event(self, event: Event) -> None:
        # Discard the event if it's not meant for us
        event_device_label = event.data.get("device_label")
        if event_device_label is None or event_device_label != self._device_information.device_label:
            _LOGGER.debug(f"Discarding {EVENT_DISCOVER_SOURCES} event for device label {event_device_label}")

        # Ignore concurrent events
        if not self._update_sources_lock.locked():
            async with self._update_sources_lock:
                # Clear any existing items first
                self._source_bidict.clear()
                await self.populate_source_bidict()

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

        _LOGGER.info(f"{self.name} source list populated with {len(self.source_list)} sources")
