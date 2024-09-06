import logging

from homeassistant.components.media_player import MediaPlayerEntity

from custom_components.vinx import LW3

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    # Extract stored runtime data
    lw3_device: LW3 = entry.runtime_data
    _LOGGER.info(lw3_device)


class VinxEncoder(MediaPlayerEntity):
    pass


class VinxDecoder(MediaPlayerEntity):
    pass
