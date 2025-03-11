from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from custom_components.vinx import DeviceInformation


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
