from io import IOBase
import zlib
from math import ceil
import mmap
from typing import cast, Dict, List, Optional, Tuple

from .common import Mixin, FileNotFoundError, NotAFileError, ReadError
from .superblock import Superblock
from .info import Info
from .fragment import FragmentBlockEntry
from .inode import Inode
from .dentry import DirectoryEntry


class Image(Mixin):
    def __init__(self, file: str) -> None:
        self.fp: Optional[IOBase] = open(file, "rb")
        mm = mmap.mmap(cast(IOBase, self.fp).fileno(), 0, prot=mmap.PROT_READ)
        self.mm = memoryview(mm)
        # UID/GID table idx -> UID/GID
        self.ids: Dict[int, int] = {}
        self.inode_table: memoryview = memoryview(b"")
        # offset from inode_table_start -> offset from the head of inode_table
        self.inode_table_index: Dict[int, int] = {}
        self.directory_table: memoryview = memoryview(b"")
        # offset from directory_table_start ->  offset from the head of directory_table
        self.directory_table_index: Dict[int, int] = {}
        self.fragments: Dict[int, FragmentBlockEntry] = {}
        self.xattrs: Dict[int, Dict[bytes, bytes]] = {}
        self.sblk = Superblock()

        self.sblk.read(self.mm, 0)
        self._read_id_table()
        self._decompress_inode_table()
        self._decompress_directory_table()
        if not self.sblk.flags & 0x0010:
            self._read_fragment_table()
        if not self.sblk.flags & 0x0200:
            self._read_xattr_table()
        blk = (self.sblk.root_inode_ref >> 16) & 0xffffffff
        offset = self.sblk.root_inode_ref & 0xffff
        self.root_inode = self._read_inode(blk, offset)

    def get_inode(self, path: str) -> Inode:
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

        return inode

    def open(self, path: str) -> bytes:
        inode = self.get_inode(path)

        if not inode.is_file:
            raise NotAFileError

        buffer = b""
        offset = inode.blks_start

        for size in inode.blk_sizes:
            if size & (1 << 24):
                size = size ^ (1 << 24)
                blk =self.mm[offset:offset+size].tobytes()
            else:
                blk = zlib.decompress(self.mm[offset:offset+size])

            buffer += blk
            offset += size

        # File contains a fragment
        frag_idx = inode.fragment_blk_index
        if frag_idx != 0xffffffff:
            start = self.fragments[frag_idx].start
            size = self.fragments[frag_idx].size
            if self.fragments[frag_idx].is_compressed:
                fragment = zlib.decompress(self.mm[start:start+size])
            else:
                fragment = self.mm[start:start+size].tobytes()

            frag_offset = inode.blk_offset
            frag_size = inode.file_size % self.sblk.blk_size
            buffer += fragment[frag_offset:frag_offset+frag_size]

        return buffer

    def listdir(self, path:str="") -> List[str]:
        return [dent.name.decode() for dent in
                self._read_dentries(self.get_inode(path))]

    def stat(self, path: str) -> Info:
        inode = self.get_inode(path)
        info = Info(self, inode)

        return info

    def _read_dentries(self, inode: Inode) -> List[DirectoryEntry]:
        dentries = []
        start = self.directory_table_index[inode.blk_idx] + inode.blk_offset
        end = start + inode.file_size - 3

        while start < end:
            count, start = self._read_uint32(self.directory_table, start)
            inode_blk, start = self._read_uint32(self.directory_table, start)
            inode_no, start = self._read_uint32(self.directory_table, start)

            if count >= 256:
                raise ReadError("Too many directory entries")

            for _ in range(count + 1):
                dent = DirectoryEntry()
                start = dent.read(self.directory_table, start)
                dent.blk = inode_blk
                dent.inode = inode_no + dent.inode_offset
                dentries.append(dent)

        return dentries

    def _read_inode(self, blk: int, offset: int) -> Inode:
        inode = Inode(self.sblk)
        inode.read(self.inode_table, self.inode_table_index[blk] + offset)

        return inode

    def _decompress_inode_table(self) -> None:
        start = self.sblk.inode_table_start
        end = self.sblk.directory_table_start
        inode_table = b""
        offset = 0

        while start < end:
            offset2 = start - self.sblk.inode_table_start
            self.inode_table_index[offset2] = offset
            blk, start = self._decompress_blk(start)
            inode_table += blk
            offset += len(blk)

        self.inode_table = memoryview(inode_table)

    def _read_id_table(self) -> None:
        offset = self.sblk.id_table_start
        buffer = b""

        for _ in range(ceil(self.sblk.id_count / 2048)):
            offset2, offset = self._read_uint64(self.mm, offset)

            blk, _ = self._decompress_blk(offset2)
            buffer += blk

        offset = 0
        for i in range(self.sblk.id_count):
            self.ids[i], offset = self._read_uint32(memoryview(buffer), offset)

    def _decompress_directory_table(self) -> None:
        start = self.sblk.directory_table_start
        end = self.sblk.fragment_table_start
        directory_table = b""
        offset = 0

        while start < end:
            offset2 = start - self.sblk.directory_table_start
            self.directory_table_index[offset2] = offset
            blk, start = self._decompress_blk(start)
            directory_table += blk
            offset += len(blk)

        self.directory_table = memoryview(directory_table)

    def _read_fragment_table(self) -> None:
        offset = self.sblk.fragment_table_start
        buffer = b""

        for _ in range(ceil(self.sblk.fragment_entry_count / 512)):
            offset2, offset = self._read_uint64(self.mm, offset)

            blk, _ = self._decompress_blk(offset2)
            buffer += blk

        offset = 0
        for i in range(self.sblk.fragment_entry_count):
            entry = FragmentBlockEntry()
            offset = entry.read(memoryview(buffer), offset)

            self.fragments[i] = entry

    def _read_xattr_table(self) -> None:
        if self.sblk.xattr_id_table_start == 0xffffffffffffffff:
            return

        offset = self.sblk.xattr_id_table_start
        # holds the decompressed xattr lookup table
        buffer = b""

        # Parse the xattr ID table and decompress the xattr lookup table
        xattr_table_start, offset = self._read_uint64(self.mm, offset)

        xattr_ids, offset = self._read_uint32(self.mm, offset)
        _, offset = self._read_uint32(self.mm, offset)

        start = xattr_table_start
        end, _ = self._read_uint64(self.mm, offset)

        for _ in range(ceil(xattr_ids / 512)):
            offset2, offset = self._read_uint64(self.mm, offset)
            block, _ = self._decompress_blk(offset2)
            buffer += block

        xattr_lookup_table = memoryview(buffer)

        offset = 0
        buffer2 = b""
        # starting pos of block -> offset in decompressed buffer
        xattr_table_index = {}
        while start < end:
            xattr_table_index[start - xattr_table_start] = offset
            block, start = self._decompress_blk(start)
            buffer2 += block
            offset += len(block)

        xattr_table = memoryview(buffer2)

        # Parse the loopkup table and KV entries
        # TODO Add a class for loopkup table entries?
        offset = 0
        for i in range(xattr_ids):
            xattr_ref, offset = self._read_uint64(xattr_lookup_table, offset)
            count, offset = self._read_uint32(xattr_lookup_table, offset)
            _, offset = self._read_uint32(xattr_lookup_table, offset)

            blk = (xattr_ref >> 16) & 0xffffffff
            offset2 = xattr_table_index[blk] + (xattr_ref & 0xffff)

            self.xattrs[i] = {}

            for _ in range(count):
                typ, offset2 = self._read_uint16(xattr_table, offset2)
                name_size, offset2 = self._read_uint16(xattr_table, offset2)
                name, offset2 = self._read_string(xattr_table, offset2, name_size)
                value_size, offset2 = self._read_uint32(xattr_table, offset2)

                # value is stored out of line
                if typ & 0x0100:
                    val, offset2 = self._read_uint64(xattr_table, offset2)
                    value_blk = (val >> 16) & 0xffffffff
                    value_offset = xattr_table_index[value_blk] + (val & 0xffff)

                    value_size, value_offset = self._read_uint32(xattr_table, value_offset)
                    value = xattr_table[value_offset:value_offset+value_size].tobytes()
                else:
                    value, offset2 = self._read_string(xattr_table, offset2, value_size)

                if typ & 0xff == 0:
                    name = b"user." + name
                elif typ & 0xff == 1:
                    name = b"trusted." + name
                elif typ & 0xff == 2:
                    name = b"security." + name
                else:
                    raise ReadError("Unknown xattr prefix type")

                self.xattrs[i][name] = value

    def _decompress_blk(self, offset: int) -> Tuple[bytes, int]:
        header, offset = self._read_uint16(self.mm, offset)
        data_size = header & 0x7fff
        is_compressed = not header & 0x8000

        data, offset = self._read_string(self.mm, offset, data_size)
        if is_compressed:
            data = zlib.decompress(data)

        return data, offset

    def close(self) -> None:
        if self.fp is None:
            return

        self.fp.close()
        self.fp = None

    def __enter__(self): # type: ignore
        return self

    def __exit__(self, exc_type, exc_value, traceback): # type: ignore
        self.close()
