from unittest import TestCase

from custom_components.vinx.lw3 import (
    ErrorResponse,
    MethodResponse,
    NodeResponse,
    PropertyResponse,
    ResponseType,
    get_response_type,
    parse_response,
    parse_single_line_response,
)


class TestResponseParsing(TestCase):
    def test_get_response_type(self):
        self.assertEqual(ResponseType.Error, get_response_type("nE FOO %E0001:Syntax error"))
        self.assertEqual(ResponseType.Property, get_response_type("pr /.ProductName=VINX"))
        self.assertEqual(ResponseType.Node, get_response_type("n- /SYS"))
        self.assertEqual(ResponseType.Method, get_response_type("m- reset()"))

    def test_parse_single_line_response(self):
        raw_response = "n- /LOGIN"
        response = parse_single_line_response(raw_response)
        self.assertIsInstance(response, NodeResponse)
        self.assertDictEqual({"prefix": "n-", "path": "/LOGIN"}, response.__dict__)

        raw_response = "-E HURR %E001:Syntax error"
        response = parse_single_line_response(raw_response)
        self.assertIsInstance(response, ErrorResponse)
        self.assertDictEqual(
            {"prefix": "-E", "path": "HURR", "code": "E001", "message": "Syntax error"}, response.__dict__
        )

        raw_response = "pr /.ProductName=VINX-110-HDMI-DEC"
        response = parse_single_line_response(raw_response)
        self.assertIsInstance(response, PropertyResponse)
        self.assertDictEqual(
            {
                "prefix": "pr",
                "path": "/.ProductName",
                "value": "VINX-110-HDMI-DEC",
            },
            response.__dict__,
        )

        raw_response = "m- /SYS:factoryDefaults"
        response = parse_single_line_response(raw_response)
        self.assertIsInstance(response, MethodResponse)
        self.assertDictEqual(
            {
                "prefix": "m-",
                "path": "/SYS",
                "name": "factoryDefaults",
            },
            response.__dict__,
        )

    def test_parse_response(self):
        raw_response = """{0000\r
n- /LOGIN\r
n- /MEDIA\r
n- /SYS\r
n- /MANAGEMENT\r
n- /DISCOVERY\r
n- /EDID\r
pr /.ProductName=VINX-110-HDMI-DEC\r
pr /.ProductPartNumber=91810003\r
pr /.SerialNumber=E8013A\r
pr /.MacAddress=00:11:AA:E8:01:3A\r
pr /.PackageVersion=v3.2.2b3 r1\r
pr /.FirmwareVersion=7.4.1\r
pr /.CoreVersion=v3.2.2b1 r1\r
}
"""
        response = parse_response(raw_response)
        self.assertEqual(13, len(response))

        first = response[0]
        self.assertIsInstance(first, NodeResponse)
        self.assertEqual("n-", first.prefix)
        self.assertEqual("/LOGIN", first.path)
        last = response[12]
        self.assertIsInstance(last, PropertyResponse)
        self.assertEqual("pr", last.prefix)
        self.assertEqual("/.CoreVersion", last.path)
        self.assertEqual("v3.2.2b1 r1", last.value)
