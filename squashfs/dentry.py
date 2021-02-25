from .common import Mixin


class DirectoryEntry(Mixin):
    def __init__(self):
        self.blk = 0
        self.offset = 0
        self.inode = 0
        self.inode_offset = 0
        self.type = 0
        self.name_size = 0
        self.name = b""

    def read(self, mm, offset=0):
        self.offset, offset = self._read_uint16(mm, offset)
        self.inode_offset, offset = self._read_int16(mm, offset)
        self.type, offset = self._read_uint16(mm, offset)
        self.name_size, offset = self._read_uint16(mm, offset)
        self.name, offset = self._read_string(mm, offset, self.name_size + 1)

        return offset
