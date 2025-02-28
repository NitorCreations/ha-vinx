from dataclasses import dataclass
from enum import Enum

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.entity import Entity
from pylw3 import LW3

from custom_components.vinx.const import DOMAIN

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.BUTTON]


class DeviceType(Enum):
    ENCODER = "encoder"
    DECODER = "decoder"
    UNKNOWN = "unknown"


@dataclass
class DeviceInformation:
    mac_address: str
    product_name: str
    device_label: str
    device_info: DeviceInfo

    def get_device_type(self) -> DeviceType:
        if self.product_name.endswith("ENC"):
            return DeviceType.ENCODER
        elif self.product_name.endswith("DEC"):
            return DeviceType.DECODER
        else:
            return DeviceType.UNKNOWN


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

        return DeviceInformation(mac_address, product_name, device_label, device_info)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    if "host" in entry.data and "port" in entry.data:
        lw3 = LW3(entry.data["host"], entry.data["port"])
    else:
        raise KeyError("Config entry is missing required parameters")

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


class VinxEntity(Entity):
    """
    Base class for all entities, provides boilerplate for determining entity unique ID,
    name and associating with the device.
    """

    def __init__(self, device_information: DeviceInformation, name: str, unique_id: str) -> None:
        self._device_information = device_information
        self._name = name
        self._unique_id = unique_id

    @property
    def unique_id(self) -> str:
        return f"vinx_{self._device_information.mac_address}_{self._unique_id}"

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_information.device_info

    @property
    def name(self) -> str:
        # Use increasingly less descriptive names depending on what information is available
        device_label = self._device_information.device_label
        serial_number = self._device_information.device_info.get("serial_number")

        if device_label:
            return f"{self._device_information.device_label} {self._name}"
        elif serial_number:
            return f"VINX {serial_number} {self._name}"
        else:
            return f"VINX {self._name}"
