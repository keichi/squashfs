from enum import Enum
from math import ceil
from typing import List

from .common import Mixin, SquashError
from .dentry import DirectoryIndex
from .superblock import Superblock


class InodeType(Enum):
    DIRECTORY = 1
    FILE = 2
    SYMLINK = 3
    BLOCK_DEVICE = 4
    CHAR_DEVICE = 5
    FIFO = 6
    SOCKET = 7
    EX_DIRECTORY = 8
    EX_FILE = 9
    EX_SYMLINK = 10
    EX_BLOCK_DEVICE = 11
    EX_CHAR_DEVICE = 12
    EX_FIFO = 13
    EX_SOCKET = 14


class Inode(Mixin):
    def __init__(self, sblk: Superblock) -> None:
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

        self.blks_start = 0
        self.fragment_blk_index = 0
        self.blk_offset = 0
        self.file_size = 0
        self.blk_sizes: List[int] = []

        self.target_size = 0
        self.target_path = b""

        self.device = 0
        self.xattr_idx = 0xFFFFFFFF

    @property
    def is_dir(self) -> bool:
        return (
            self.inode_type == InodeType.DIRECTORY.value
            or self.inode_type == InodeType.EX_DIRECTORY.value
        )

    @property
    def is_symlink(self) -> bool:
        return (
            self.inode_type == InodeType.SYMLINK.value
            or self.inode_type == InodeType.EX_SYMLINK.value
        )

    @property
    def is_file(self) -> bool:
        return (
            self.inode_type == InodeType.FILE.value
            or self.inode_type == InodeType.EX_FILE.value
        )

    @property
    def is_block_dev(self) -> bool:
        return (
            self.inode_type == InodeType.BLOCK_DEVICE.value
            or self.inode_type == InodeType.EX_BLOCK_DEVICE.value
        )

    @property
    def is_char_dev(self) -> bool:
        return (
            self.inode_type == InodeType.CHAR_DEVICE.value
            or self.inode_type == InodeType.EX_CHAR_DEVICE.value
        )

    @property
    def is_fifo(self) -> bool:
        return (
            self.inode_type == InodeType.FIFO.value
            or self.inode_type == InodeType.EX_FIFO.value
        )

    @property
    def is_socket(self) -> bool:
        return (
            self.inode_type == InodeType.SOCKET.value
            or self.inode_type == InodeType.EX_SOCKET.value
        )

    def read(self, mm: memoryview, offset: int) -> int:
        self.inode_type, offset = self._read_uint16(mm, offset)
        self.permissions, offset = self._read_uint16(mm, offset)
        self.uid_idx, offset = self._read_uint16(mm, offset)
        self.gid_idx, offset = self._read_uint16(mm, offset)
        self.modified_time, offset = self._read_uint32(mm, offset)
        self.inode_number, offset = self._read_uint32(mm, offset)

        # Basic directory
        if self.inode_type == InodeType.DIRECTORY.value:
            self.blk_idx, offset = self._read_uint32(mm, offset)
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.file_size, offset = self._read_uint16(mm, offset)
            self.blk_offset, offset = self._read_uint16(mm, offset)
            self.parent_inode_number, offset = self._read_uint32(mm, offset)

            return offset

        # Basic file
        elif self.inode_type == InodeType.FILE.value:
            self.blks_start, offset = self._read_uint32(mm, offset)
            self.fragment_blk_index, offset = self._read_uint32(mm, offset)
            self.blk_offset, offset = self._read_uint32(mm, offset)
            self.file_size, offset = self._read_uint32(mm, offset)

            self.blk_sizes = []

            # File does not end with a fragment
            if self.fragment_blk_index == 0xFFFFFFFF:
                num_blks = ceil(self.file_size / self.sblk.blk_size)
            else:
                num_blks = self.file_size // self.sblk.blk_size

            for _ in range(num_blks):
                size, offset = self._read_uint32(mm, offset)
                self.blk_sizes.append(size)

            return offset

        # Basic symlink
        elif self.inode_type == InodeType.SYMLINK.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.target_size, offset = self._read_uint32(mm, offset)
            self.target_path, offset = self._read_string(mm, offset, self.target_size)

            return offset

        # Basic block device
        elif self.inode_type == InodeType.BLOCK_DEVICE.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.device, offset = self._read_uint32(mm, offset)

            return offset

        # Basic char device
        elif self.inode_type == InodeType.CHAR_DEVICE.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.device, offset = self._read_uint32(mm, offset)

            return offset

        # Basic fifo
        elif self.inode_type == InodeType.FIFO.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)

            return offset

        # Basic socket
        elif self.inode_type == InodeType.SOCKET.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)

            return offset

        # Extended directory
        elif self.inode_type == InodeType.EX_DIRECTORY.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.file_size, offset = self._read_uint32(mm, offset)
            self.blk_idx, offset = self._read_uint32(mm, offset)
            self.parent_inode_number, offset = self._read_uint32(mm, offset)
            self.index_count, offset = self._read_uint16(mm, offset)
            self.blk_offset, offset = self._read_uint16(mm, offset)
            self.xattr_idx, offset = self._read_uint32(mm, offset)

            self.index = []

            for _ in range(self.index_count):
                dindex = DirectoryIndex()
                offset = dindex.read(mm, offset)
                self.index.append(dindex)

            return offset

        # Extended file
        elif self.inode_type == InodeType.EX_FILE.value:
            self.blks_start, offset = self._read_uint64(mm, offset)
            self.file_size, offset = self._read_uint64(mm, offset)
            self.sparse, offset = self._read_uint64(mm, offset)
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.fragment_blk_index, offset = self._read_uint32(mm, offset)
            self.blk_offset, offset = self._read_uint32(mm, offset)
            self.xattr_idx, offset = self._read_uint32(mm, offset)

            # File does not end with a fragment
            if self.fragment_blk_index == 0xFFFFFFFF:
                num_blks = ceil(self.file_size / self.sblk.blk_size)
            else:
                num_blks = self.file_size // self.sblk.blk_size

            self.blk_sizes = []

            for _ in range(num_blks):
                size, offset = self._read_uint32(mm, offset)
                self.blk_sizes.append(size)

            return offset

        # Extended symlink
        elif self.inode_type == InodeType.EX_SYMLINK.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.target_size, offset = self._read_uint32(mm, offset)
            self.target_path, offset = self._read_string(mm, offset, self.target_size)
            self.xattr_idx, offset = self._read_uint32(mm, offset)

            return offset

        # Extended block device
        elif self.inode_type == InodeType.EX_BLOCK_DEVICE.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.device, offset = self._read_uint32(mm, offset)
            self.xatttr_idx, offset = self._read_uint32(mm, offset)

            return offset

        # Extended char device
        elif self.inode_type == InodeType.EX_CHAR_DEVICE.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.device, offset = self._read_uint32(mm, offset)
            self.xatttr_idx, offset = self._read_uint32(mm, offset)

            return offset

        # Extended fifo
        elif self.inode_type == InodeType.EX_FIFO.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.xatttr_idx, offset = self._read_uint32(mm, offset)

            return offset

        # Extended socket
        elif self.inode_type == InodeType.EX_BLOCK_DEVICE.value:
            self.hard_link_count, offset = self._read_uint32(mm, offset)
            self.xatttr_idx, offset = self._read_uint32(mm, offset)

            return offset

        # Unknown inode type
        else:
            raise SquashError(f"Unknown inode type {self.inode_type}")
