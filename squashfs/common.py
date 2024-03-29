import struct

from typing import Tuple


class SquashError(Exception):
    pass


class ReadError(SquashError):
    pass


class FileNotFoundError(SquashError):
    pass


class NotAFileError(SquashError):
    pass


class Mixin:
    def _read_int16(self, mm: memoryview, offset: int) -> Tuple[int, int]:
        (val,) = struct.unpack_from("<h", mm, offset)
        return val, offset + 2

    def _read_uint16(self, mm: memoryview, offset: int) -> Tuple[int, int]:
        (val,) = struct.unpack_from("<H", mm, offset)
        return val, offset + 2

    def _read_uint32(self, mm: memoryview, offset: int) -> Tuple[int, int]:
        (val,) = struct.unpack_from("<I", mm, offset)
        return val, offset + 4

    def _read_uint64(self, mm: memoryview, offset: int) -> Tuple[int, int]:
        (val,) = struct.unpack_from("<Q", mm, offset)
        return val, offset + 8

    def _read_string(self, mm: memoryview, offset: int, size: int) -> Tuple[bytes, int]:
        return mm[offset : offset + size].tobytes(), offset + size
