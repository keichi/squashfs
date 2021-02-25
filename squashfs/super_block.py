from .common import Mixin


class Superblock(Mixin):
    def __init__(self):
        self.magic = 0
        self.inode_count = 0
        self.modification_time = 0
        self.blk_size = 0
        self.fragment_entry_count = 0
        self.compression_id = 0
        self.blk_log = 0
        self.flags = 0
        self.id_count = 0
        self.version_major = 0
        self.version_minor = 0
        self.root_inode_ref = 0
        self.bytes_used = 0
        self.id_table_start = 0
        self.xattr_id_table_start = 0
        self.inode_table_start = 0
        self.directory_table_start = 0
        self.fragment_table_start = 0
        self.export_table_start = 0

    def read(self, mm, offset=0):
        self.magic, offset = self._read_uint32(mm, offset)
        assert(self.magic == 0x73717368)

        self.inode_count, offset = self._read_uint32(mm, offset)
        self.modification_time, offset = self._read_uint32(mm, offset)
        self.blk_size, offset = self._read_uint32(mm, offset)
        self.fragment_entry_count, offset = self._read_uint32(mm, offset)
        self.compression_id, offset = self._read_uint16(mm, offset)
        self.blk_log, offset = self._read_uint16(mm, offset)
        assert(1 << self.blk_log == self.blk_size)

        self.flags, offset = self._read_uint16(mm, offset)
        self.id_count, offset = self._read_uint16(mm, offset)
        self.version_major, offset = self._read_uint16(mm, offset)
        self.version_minor, offset = self._read_uint16(mm, offset)
        assert((self.version_major, self.version_minor) == (4, 0))

        self.root_inode_ref, offset = self._read_uint64(mm, offset)
        self.bytes_used, offset = self._read_uint64(mm, offset)
        self.id_table_start, offset = self._read_uint64(mm, offset)
        self.xattr_id_table_start, offset = self._read_uint64(mm, offset)
        self.inode_table_start, offset = self._read_uint64(mm, offset)
        self.directory_table_start, offset = self._read_uint64(mm, offset)
        self.fragment_table_start, offset = self._read_uint64(mm, offset)
        self.export_table_start, offset = self._read_uint64(mm, offset)

        return offset
