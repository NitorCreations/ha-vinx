import asyncio
import re

from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass


@dataclass
class Response:
    prefix: str
    path: str


@dataclass
class PropertyResponse(Response):
    value: str

    def __str__(self):
        return self.value


@dataclass
class ErrorResponse(Response):
    code: int
    message: str

    def __str__(self):
        return self.message


class LW3:
    def __init__(self, hostname: str, port: int, timeout: int = 5):
        self._hostname = hostname
        self._port = port
        self._timeout = timeout
        self._reader: StreamReader | None = None
        self._writer: StreamWriter | None = None
        self._semaphore = asyncio.Semaphore()

    async def _read_until(self, phrase: str) -> str | None:
        b = bytearray()

        while not self._reader.at_eof():
            byte = await self._reader.read(1)
            b += byte

            if b.endswith(phrase.encode()):
                return b.decode()

    async def connect(self):
        self._reader, self._writer = await asyncio.open_connection(self._hostname, self._port)

    @staticmethod
    def _is_error_response(response: str) -> bool:
        return response[1] == "E"

    @staticmethod
    def parse_response(response: str) -> PropertyResponse | ErrorResponse:
        if LW3._is_error_response(response):
            matches = re.search(r"^(.E) (.*) %(E[0-9]+):(.*)$", response)
            return ErrorResponse(matches.group(1), matches.group(2), matches.group(3), matches.group(4))

        matches = re.fullmatch(r"^(.*) (.*)=(.*)$", response)
        return PropertyResponse(matches.group(1), matches.group(2), matches.group(3))

    async def _read_and_parse_response(self) -> PropertyResponse:
        response = await self._read_until("\r\n")

        if response is None:
            raise EOFError("Reached EOF while reading, connection probably lost")

        result = self.parse_response(response.strip())

        if isinstance(result, ErrorResponse):
            raise ValueError(result)

        return result

    async def _run_get_property(self, path: str) -> PropertyResponse:
        async with self._semaphore:
            self._writer.write(f"GET {path}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def _run_set_property(self, path: str, value: str) -> PropertyResponse:
        async with self._semaphore:
            self._writer.write(f"SET {path}={value}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def get_property(self, path: str) -> PropertyResponse:
        return await asyncio.wait_for(self._run_get_property(path), self._timeout)

    async def set_property(self, path: str, value: str) -> PropertyResponse:
        return await asyncio.wait_for(self._run_set_property(path, value), self._timeout)

    async def get_product_name(self):
        return str(await self._run_get_property("/.ProductName"))

    async def get_serial_number(self):
        return str(await self._run_get_property("/.SerialNumber"))

    async def get_mac_address(self):
        return str(await self._run_get_property("/.MacAddress"))
