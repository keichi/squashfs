from .common import Mixin


class DirectoryEntry(Mixin):
    def __init__(self) -> None:
        self.blk = 0
        self.offset = 0
        self.inode = 0
        self.inode_offset = 0
        self.type = 0
        self.name_size = 0
        self.name = b""

    def read(self, mm: memoryview, offset: int) -> int:
        self.offset, offset = self._read_uint16(mm, offset)
        self.inode_offset, offset = self._read_int16(mm, offset)
        self.type, offset = self._read_uint16(mm, offset)
        self.name_size, offset = self._read_uint16(mm, offset)
        self.name, offset = self._read_string(mm, offset, self.name_size + 1)

        return offset


class DirectoryIndex(Mixin):
    def __init__(self) -> None:
        self.index = 0
        self.start = 0
        self.name_size = 0
        self.name = b""

    def read(self, mm: memoryview, offset: int) -> int:
        self.index, offset = self._read_uint32(mm, offset)
        self.start, offset = self._read_uint32(mm, offset)
        self.name_size, offset = self._read_uint32(mm, offset)
        self.name, offset = self._read_string(mm, offset, self.name_size + 1)

        return offset
