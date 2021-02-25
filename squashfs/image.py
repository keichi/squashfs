import zlib
from collections import deque
from math import ceil

from .common import Mixin
from .superblock import Superblock
from .inode import Inode
from .dentry import DirectoryEntry


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
        self.traverse(blk, offset)

    def traverse(self, blk, offset):
        stack = deque([(self._read_inode(blk, offset), b"")])

        while stack:
            inode, path = stack.pop()
            print(path.decode())

            if inode.inode_type == 1 or inode.inode_type == 8:
                dents = self._read_dents(inode)
                for dent in reversed(dents):
                    child_inode = self._read_inode(dent.blk, dent.offset)
                    child_path = path + b"/" + dent.name

                    stack.append((child_inode, child_path))

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

        for _ in range(ceil(self.sblk.id_count / 2048)):
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
        header, offset = self._read_uint16(self.mm, offset)
        data_size = header & 0x7fff
        is_compressed = not header & 0x8000

        data, offset = self._read_string(self.mm, offset, data_size)
        if is_compressed:
            data = zlib.decompress(data)

        return data, offset
