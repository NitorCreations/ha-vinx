import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory

from custom_components.vinx import LW3, DeviceInformation, DeviceType, VinxRuntimeData
from custom_components.vinx.const import EVENT_DISCOVER_SOURCES
from custom_components.vinx.entity import VinxEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(_hass, entry: ConfigEntry, async_add_entities):
    # Extract stored runtime data
    runtime_data: VinxRuntimeData = entry.runtime_data
    _LOGGER.info(f"Runtime data: {runtime_data}")

    # Add reboot button entity
    async_add_entities([VinxRebootButtonEntity(runtime_data.lw3, runtime_data.device_information)])

    # Add discover sources button for decoders
    device_type = runtime_data.device_information.get_device_type()

    if device_type == DeviceType.DECODER:
        async_add_entities([VinxDiscoverSourcesButtonEntity(runtime_data.device_information)])


class VinxRebootButtonEntity(VinxEntity, ButtonEntity):
    def __init__(self, lw3: LW3, device_information: DeviceInformation) -> None:
        super().__init__(device_information, "reboot button", "reboot_button")
        self._lw3 = lw3

    _attr_device_class = ButtonDeviceClass.RESTART

    async def async_press(self) -> None:
        async with self._lw3.connection():
            _LOGGER.info("Issuing device reset")
            await self._lw3.call("/SYS", "reset(1)")


class VinxDiscoverSourcesButtonEntity(VinxEntity, ButtonEntity):
    def __init__(self, device_information: DeviceInformation):
        super().__init__(device_information, "discover sources button", "discover_sources_button")

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        self.hass.bus.async_fire(
            EVENT_DISCOVER_SOURCES,
            {
                # The same event is sent to all event listeners, but we only want the decoder entity belonging to the
                # same device as this button to handle the event, so send an identifier here that can be checked in the
                # listener
                "device_label": self._device_information.device_label,
            },
        )
