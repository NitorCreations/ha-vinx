import asyncio
import re

from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass
from enum import Enum


@dataclass
class SingleLineResponse:
    prefix: str
    path: str


@dataclass
class PropertyResponse(SingleLineResponse):
    value: str

    def __str__(self):
        return self.value


@dataclass
class ErrorResponse(SingleLineResponse):
    code: int
    message: str

    def __str__(self):
        return self.message


@dataclass
class NodeResponse(SingleLineResponse):
    pass


@dataclass
class MethodResponse(SingleLineResponse):
    name: str

    def __str__(self):
        return self.name


type MultiLineResponse = list[SingleLineResponse]
type Response = SingleLineResponse | MultiLineResponse


class ResponseType(Enum):
    Node = 1
    Property = 2
    Error = 3
    Method = 4


def get_response_type(response: str) -> ResponseType:
    if response[1] == "E":
        return ResponseType.Error
    elif response[0] == "p":
        return ResponseType.Property
    elif response[0] == "n":
        return ResponseType.Node
    elif response[0] == "m":
        return ResponseType.Method

    raise ValueError("Unknown response type")


def parse_single_line_response(response: str) -> SingleLineResponse:
    match get_response_type(response):
        case ResponseType.Error:
            matches = re.search(r"^(.E) (.*) %(E[0-9]+):(.*)$", response)
            return ErrorResponse(matches.group(1), matches.group(2), matches.group(3), matches.group(4))
        case ResponseType.Property:
            matches = re.fullmatch(r"^p(.*) (.*)=(.*)$", response)
            return PropertyResponse(f"p{matches.group(1)}", matches.group(2), matches.group(3))
        case ResponseType.Node:
            matches = re.fullmatch(r"^n(.*) (.*)$", response)
            return NodeResponse(f"n{matches.group(1)}", matches.group(2))
        case ResponseType.Method:
            matches = re.fullmatch(r"^m(.*) (.*):(.*)$", response)
            return MethodResponse(f"m{matches.group(1)}", matches.group(2), matches.group(3))


def parse_multiline_response(lines: list[str]) -> MultiLineResponse:
    responses = []

    for response in lines:
        responses.append(parse_single_line_response(response))

    return responses


def parse_response(response: str) -> Response:
    lines = response.split("\r\n")

    # Determine if we're dealing with a single line response or multiple
    if len(lines) == 3:
        return parse_single_line_response(lines[1])
    else:
        return parse_multiline_response(lines[1 : len(lines) - 1])


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

    def connection(self):
        return LW3ConnectionContext(self)

    async def _connect(self):
        self._reader, self._writer = await asyncio.open_connection(self._hostname, self._port)

    async def _disconnect(self):
        self._writer.close()
        await self._writer.wait_closed()

    async def _read_and_parse_response(self) -> Response:
        # All commands are wrapped with a signature, so read until the end delimiter
        response = await self._read_until("}")

        if response is None:
            raise EOFError("Reached EOF while reading, connection probably lost")

        result = parse_response(response.strip())

        if isinstance(result, ErrorResponse):
            raise ValueError(result)

        return result

    async def _run_get(self, path: str) -> Response:
        async with self._semaphore:
            self._writer.write(f"0000#GET {path}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def _run_set(self, path: str, value: str) -> Response:
        async with self._semaphore:
            self._writer.write(f"0000#SET {path}={value}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def _run_get_all(self, path: str) -> Response:
        async with self._semaphore:
            self._writer.write(f"0000#GETALL {path}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def get_property(self, path: str) -> PropertyResponse:
        response = await asyncio.wait_for(self._run_get(path), self._timeout)

        if not isinstance(response, PropertyResponse):
            raise ValueError(f"Requested path {path} does not return a property")

        return response

    async def set_property(self, path: str, value: str) -> PropertyResponse:
        response = await asyncio.wait_for(self._run_set(path, value), self._timeout)

        if not isinstance(response, PropertyResponse):
            raise ValueError(f"Requested path {path} does not return a property")

        return response

    async def get_all(self, path: str) -> Response:
        return await asyncio.wait_for(self._run_get_all(path), self._timeout)


class LW3ConnectionContext:
    def __init__(self, lw3: LW3):
        self._lw3 = lw3

    async def __aenter__(self):
        await self._lw3._connect()

    async def __aexit__(self, *args):
        await self._lw3._disconnect()
