import zlib
from collections import deque
from math import ceil

from .common import Mixin, FileNotFoundError, NotAFileError, ReadError
from .superblock import Superblock
from .file import File
from .fragment import FragmentBlockEntry
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
        self.fragments = {}
        self.sblk = Superblock()

        self.sblk.read(self.mm, offset)
        self._read_id_table()
        self._decompress_inode_table()
        self._decompress_directory_table()
        self._read_fragment_table()

        blk = (self.sblk.root_inode_ref >> 16) & 0xffffffff
        offset = self.sblk.root_inode_ref & 0xffff
        self.root_inode = self._read_inode(blk, offset)

    def open(self, path):
        inode = self.root_inode

        for p in path.split("/"):
            if not p:
                continue

            found = False
            dentries = self._read_dentries(inode)
            for dent in dentries:
                if p == dent.name.decode():
                    inode = self._read_inode(dent.blk, dent.offset)
                    found = True
                    break

            if not found:
                raise FileNotFoundError

        if not inode.is_file:
            raise NotAFileError

        return File(self, inode)

    def traverse(self, blk, offset):
        stack = deque([(self._read_inode(blk, offset), b"")])

        while stack:
            inode, path = stack.pop()
            print(path.decode())

            if inode.is_dir:
                dentries = self._read_dentries(inode)
                for dent in reversed(dentries):
                    child_inode = self._read_inode(dent.blk, dent.offset)
                    child_path = path + b"/" + dent.name

                    stack.append((child_inode, child_path))

    def _read_dentries(self, inode):
        dentries = []
        start = self.directory_table_index[inode.blk_idx] + inode.blk_offset
        end = start + inode.file_size

        while True:
            count, start = self._read_uint32(self.directory_table, start)
            inode_blk, start = self._read_uint32(self.directory_table, start)
            inode_number, start = self._read_uint32(
                self.directory_table, start)

            if start >= end:
                break

            if count >= 256:
                raise ReadError("Too many directory entries")

            for _ in range(count + 1):
                dent = DirectoryEntry()
                start = dent.read(self.directory_table, start)
                dent.blk = inode_blk
                dent.inode = inode_number + dent.inode_offset
                dentries.append(dent)

        return dentries

    def _read_inode(self, blk, offset):
        inode = Inode(self.sblk)
        inode.read(self.inode_table, self.inode_table_index[blk] + offset)

        return inode

    def _decompress_inode_table(self):
        start = self.sblk.inode_table_start
        end = self.sblk.directory_table_start
        offset = 0

        while start < end:
            offset2 = start - self.sblk.inode_table_start
            self.inode_table_index[offset2] = offset
            blk, start = self._decompress_blk(start)
            self.inode_table += blk
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
            offset2 = start - self.sblk.directory_table_start
            self.directory_table_index[offset2] = offset
            blk, start = self._decompress_blk(start)
            self.directory_table += blk
            offset += len(blk)

    def _read_fragment_table(self):
        offset = self.sblk.fragment_table_start
        buffer = b""

        for _ in range(ceil(self.sblk.fragment_entry_count / 512)):
            offset2, offset = self._read_uint64(self.mm, offset)

            blk, _ = self._decompress_blk(offset2)
            buffer += blk

        offset = 0
        for i in range(self.sblk.fragment_entry_count):
            entry = FragmentBlockEntry()
            offset = entry.read(buffer, offset)

            self.fragments[i] = entry

    def _decompress_blk(self, offset):
        header, offset = self._read_uint16(self.mm, offset)
        data_size = header & 0x7fff
        is_compressed = not header & 0x8000

        data, offset = self._read_string(self.mm, offset, data_size)
        if is_compressed:
            data = zlib.decompress(data)

        return data, offset
