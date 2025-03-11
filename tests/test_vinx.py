import unittest

from homeassistant.helpers.device_registry import DeviceInfo, format_mac

from custom_components.vinx import DeviceInformation
from custom_components.vinx.entity import VinxEntity


class VinxEntityTests(unittest.TestCase):
    def test_unique_id_and_name(self):
        device_information = DeviceInformation(
            format_mac("00:11:22:33:44:55"),
            "VINX HDMI JOTAIN",
            "engelbart-decoder",
            DeviceInfo(serial_number="123123"),
        )

        entity = VinxEntity(
            device_information,
            "media player",
            "media_player",
        )

        self.assertEqual("vinx_00:11:22:33:44:55_media_player", entity.unique_id)
        self.assertEqual("engelbart-decoder media player", entity.name)

        # Without device_label should fall back to serial number
        device_information.device_label = ""
        self.assertEqual("VINX 123123 media player", entity.name)

        # Without serial number should fall back to the most generic version
        device_information.device_info = DeviceInfo()
        self.assertEqual("VINX media player", entity.name)


if __name__ == "__main__":
    unittest.main()
