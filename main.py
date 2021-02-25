#!/usr/bin/env python3

import math
import mmap
import struct
import zlib


class SquashError(Exception):
    pass


class Mixin:
    def _read_int16(self, mm, offset):
        val, = struct.unpack_from("<h", mm, offset)
        return val, offset + 2

    def _read_uint16(self, mm, offset):
        val, = struct.unpack_from("<H", mm, offset)
        return val, offset + 2

    def _read_uint32(self, mm, offset):
        val, = struct.unpack_from("<I", mm, offset)
        return val, offset + 4

    def _read_uint64(self, mm, offset):
        val, = struct.unpack_from("<Q", mm, offset)
        return val, offset + 8

    def _read_string(self, mm, offset, size):
        return mm[offset:offset+size], offset + size


class Inode(Mixin):
    def __init__(self, sblk):
        self.sblk = sblk

        self.inode_type = 0
        self.permissions = 0
        self.uid_idx = 0
        self.gid_idx = 0
        self.modified_time = 0
        self.inode_number = 0

        self.blk_idx = 0
        self.hard_link_count = 0
        self.file_size = 0
        self.blk_offset = 0
        self.parent_inode_number = 0

        self.blk_start = 0
        self.fragment_blk_index = 0
        self.blk_offset = 0
        self.file_size = 0
        self.blk_sizes = []

        self.target_size = 0
        self.target_path = b""

    def read(self, mm, offset=0):
        self.inode_type, offset = self._read_uint16(mm, offset)
        self.permissions, offset = self._read_uint16(mm, offset)
        self.uid_idx, offset = self._read_uint16(mm, offset)
        self.gid_idx, offset = self._read_uint16(mm, offset)
        self.modified_time, offset = self._read_uint32(mm, offset)
        self.inode_number, offset = self._read_uint32(mm, offset)

        #  print("------------------------------------------------")
        #  print(f"inode_type: {self.inode_type}")
        #  print(f"permissions: {self.permissions}")
        #  print(f"uid_idx: {self.uid_idx}")
        #  print(f"gid_idx: {self.gid_idx}")
        #  print(f"modified_time: {self.modified_time}")
        #  print(f"inode_number: {self.inode_number}")

        # Basic directory
        if self.inode_type == 1:
            self.blk_idx, offset = self._read_uint32(mm, offset)
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.file_size, offset = self._read_uint16(mm, offset)
            self.blk_offset, offset = self._read_uint16(mm, offset)
            self.parent_inode_number, offset = self._read_uint32(mm, offset)

            return offset

        # Basic file
        elif self.inode_type == 2:
            self.blk_start, offset = self._read_uint32(mm, offset)
            self.fragment_blk_index, offset = self._read_uint32(mm, offset)
            self.blk_offset, offset = self._read_uint32(mm, offset)
            self.file_size, offset = self._read_uint32(mm, offset)

            self.blk_sizes = []

            # File does not end with a fragment
            if self.fragment_blk_index == 0xffffffff:
                num_blks = math.ceil(self.file_size / self.sblk.blk_size)
            else:
                num_blks = self.file_size // self.sblk.blk_size

            for i in range(num_blks):
                size, offset = self._read_uint32(mm, offset)
                self.blk_sizes.append(size)

            return offset

        # Basic symlink
        elif self.inode_type == 3:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.target_size, offset = self._read_uint32(mm, offset)
            self.target_path, offset = self._read_string(mm, offset,
                                                         self.target_size)

            return offset

        # Basic blk device
        elif self.inode_type == 4:
            raise SquashError

        # Basic char device
        elif self.inode_type == 5:
            raise SquashError

        # Basic fifo
        elif self.inode_type == 6:
            raise SquashError

        # Basic socket
        elif self.inode_type == 7:
            raise SquashError

        # Extended directory
        elif self.inode_type == 8:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.file_size, offset = self._read_uint32(mm, offset)
            self.blk_idx, offset = self._read_uint32(mm, offset)
            self.parent_inode_number, offset = self._read_uint32(mm, offset)
            self.index_count, offset = self._read_uint16(mm, offset)
            self.blk_offset, offset = self._read_uint16(mm, offset)
            self.xattr_idx, offset = self._read_uint32(mm, offset)

            self.index = []

            # TODO Create directory index objects
            for _ in range(self.index_count):
                index, offset = self._read_uint32(mm, offset)
                start, offset = self._read_uint32(mm, offset)
                name_size, offset = self._read_uint32(mm, offset)
                name, offset = self._read_string(mm, offset, name_size + 1)
                self.index.append(None)

            return offset

        # Extended file
        elif self.inode_type == 9:
            self.blk_start, offset = self._read_uint64(mm, offset)
            self.file_size, offset = self._read_uint64(mm, offset)
            self.sparse, offset = self._read_uint64(mm, offset)
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.fragment_blk_index, offset = self._read_uint32(mm, offset)
            self.blk_offset, offset = self._read_uint32(mm, offset)
            self.xattr_idx, offset = self._read_uint32(mm, offset)

            self.blk_sizes = []

            # File does not end with a fragment
            if self.fragment_blk_index == 0xffffffff:
                num_blks = math.ceil(self.file_size / self.sblk.blk_size)
            else:
                num_blks = self.file_size // self.sblk.blk_size

            for i in range(num_blks):
                size, offset = self._read_uint32(mm, offset)
                self.blk_sizes.append(size)

            return offset
        # Extended symlink
        elif self.inode_type == 10:
            raise SquashError

        # Extended blk device
        elif self.inode_type == 11:
            raise SquashError

        # Extended char device
        elif self.inode_type == 12:
            raise SquashError

        # Extended fifo
        elif self.inode_type == 13:
            raise SquashError

        # Extended socket
        elif self.inode_type == 14:
            raise SquashError

        # Unknown inode type
        else:
            raise SquashError


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


class Image(Mixin):
    def __init__(self, mm, offset=0):
        self.mm = mm
        self.ids = {}
        self.inode_table = b""
        # key: offset from inode_table_start, value: offset from the head of
        # inode_table
        self.inode_table_index = {}
        self.directory_table = b""
        # key: offset from directory_table_start -> offset, value: offset from
        # the head of directory_table
        self.directory_table_index = {}
        self.sblk = Superblock()

        self.sblk.read(self.mm, offset)
        self._read_id_table()
        self._decompress_inode_table()
        self._decompress_directory_table()

        blk = (self.sblk.root_inode_ref >> 16) & 0xffffffff
        offset = self.sblk.root_inode_ref & 0xffff
        self._traverse(b"", blk, offset)

    def _traverse(self, parent, blk, offset):
        inode = self._read_inode(blk, offset)
        dents = self._read_dents(inode)

        for dent in dents:
            name = parent + b"/" + dent.name

            print(name.decode())
            if dent.type == 1 or dent.type == 8:
                self._traverse(name, dent.blk, dent.offset)

    def _read_dents(self, inode):
        dents = []
        start = self.directory_table_index[inode.blk_idx] + inode.blk_offset
        end = start + inode.file_size

        while True:
            count, start = self._read_uint32(self.directory_table, start)
            inode_blk, start = self._read_uint32(self.directory_table, start)
            inode_number, start = self._read_uint32(
                self.directory_table, start)

            if start >= end:
                break

            assert(count < 256)

            for _ in range(count + 1):
                dent = DirectoryEntry()
                start = dent.read(self.directory_table, start)
                dent.blk = inode_blk
                dent.inode = inode_number + dent.inode_offset
                dents.append(dent)

        return dents

    def _read_inode(self, blk, offset):
        inode = Inode(self.sblk)
        inode.read(self.inode_table, self.inode_table_index[blk] + offset)

        return inode

    def _decompress_inode_table(self):
        start = self.sblk.inode_table_start
        end = self.sblk.directory_table_start
        offset = 0

        while start < end:
            tmp = start
            blk, start = self._decompress_blk(start)
            self.inode_table += blk
            self.inode_table_index[tmp - self.sblk.inode_table_start] = offset
            offset += len(blk)

    def _read_id_table(self):
        offset = self.sblk.id_table_start
        buffer = b""

        for _ in range(math.ceil(self.sblk.id_count / 2048)):
            offset2, offset = self._read_uint64(self.mm, offset)

            blk, _ = self._decompress_blk(offset2)
            buffer += blk

        offset = 0
        for i in range(self.sblk.id_count):
            self.ids[i], offset = self._read_uint16(buffer, offset)

    def _decompress_directory_table(self):
        start = self.sblk.directory_table_start
        end = self.sblk.fragment_table_start
        offset = 0

        while start < end:
            tmp = start
            blk, start = self._decompress_blk(start)
            self.directory_table += blk
            self.directory_table_index[tmp -
                                       self.sblk.directory_table_start] = offset
            offset += len(blk)

    def _decompress_blk(self, offset):
        header, = struct.unpack_from("<H", self.mm, offset=offset+0)
        data_size = header & 0x7fff
        is_compressed = not header & 0x8000

        data = self.mm[offset+2:offset+2+data_size]
        if is_compressed:
            data = zlib.decompress(data)

        return data, offset + data_size + 2


def main():
    with open("python_latest.sfs", "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        image = Image(mm)


if __name__ == "__main__":
    main()
