from .common import Mixin, ReadError



class FragmentBlockEntry(Mixin):
    def __init__(self):
        self.start = 0
        self.size = 0
        self.is_compressed = False

    def read(self, mm, offset=0):
        self.start, offset = self._read_uint64(mm, offset)
        self.size, offset = self._read_uint32(mm, offset)

        if self.size & (1 << 24):
            self.is_compressed = False
            self.size = self.size ^ (1 << 24)
        else:
            self.is_compressed = True

        if self.size > (1 << 20):
            raise ReadError("Fragment size is too large")

        offset += 4

        return offset

    def __repr__(self):
        return f"{self.__class__.__name__}(start={self.start}, size={self.size})"
