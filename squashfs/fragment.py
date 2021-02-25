from .common import Mixin


class FragmentBlockEntry(Mixin):
    def __init__(self):
        self.start = 0
        self.size = 0

    def read(self, mm, offset=0):
        self.start, offset = self._read_uint64(mm, offset)
        self.size, offset = self._read_uint32(mm, offset)
        offset += 4

        return offset
