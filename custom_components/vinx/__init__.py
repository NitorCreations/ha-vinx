from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo, format_mac

from custom_components.vinx.const import DOMAIN
from custom_components.vinx.lw3 import LW3

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]


@dataclass
class DeviceInformation:
    mac_address: str
    product_name: str
    device_info: DeviceInfo


@dataclass
class VinxRuntimeData:
    lw3: LW3
    device_information: DeviceInformation


async def get_device_information(lw3: LW3) -> DeviceInformation:
    async with lw3.connection():
        mac_address = str(await lw3.get_property("/.MacAddress"))
        product_name = str(await lw3.get_property("/.ProductName"))
        device_label = str(await lw3.get_property("/SYS/MB.DeviceLabel"))
        firmware_version = str(await lw3.get_property("/.FirmwareVersion"))
        serial_number = str(await lw3.get_property("/.SerialNumber"))
        ip_address = str(await lw3.get_property("/MANAGEMENT/NETWORK.IpAddress"))

        device_info = DeviceInfo(
            identifiers={(DOMAIN, format_mac(mac_address))},
            name=f"{device_label} ({product_name})",
            manufacturer="Lightware",
            model=product_name,
            sw_version=firmware_version,
            serial_number=serial_number,
            configuration_url=f"http://{ip_address}/",
        )

        return DeviceInformation(mac_address, product_name, device_info)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    lw3 = LW3(entry.data["host"], entry.data["port"])

    try:
        # Store runtime information
        async with lw3.connection():
            device_information = await get_device_information(lw3)

        # Store the lw3 as runtime data in the entry
        entry.runtime_data = VinxRuntimeData(lw3, device_information)
    except ConnectionError as e:
        raise ConfigEntryNotReady("Unable to connect") from e

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
