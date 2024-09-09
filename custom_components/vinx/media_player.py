import logging

from homeassistant.components.media_player import MediaPlayerEntity

from custom_components.vinx import VinxRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    # Extract stored runtime data
    runtime_data: VinxRuntimeData = entry.runtime_data
    _LOGGER.info(f"Runtime data: {runtime_data}")


class VinxEncoder(MediaPlayerEntity):
    pass


class VinxDecoder(MediaPlayerEntity):
    pass
