from math import ceil

from .common import Mixin, SquashError


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
                num_blks = ceil(self.file_size / self.sblk.blk_size)
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
            # TODO
            raise SquashError

        # Basic char device
        elif self.inode_type == 5:
            # TODO
            raise SquashError

        # Basic fifo
        elif self.inode_type == 6:
            # TODO
            raise SquashError

        # Basic socket
        elif self.inode_type == 7:
            # TODO
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
                num_blks = ceil(self.file_size / self.sblk.blk_size)
            else:
                num_blks = self.file_size // self.sblk.blk_size

            for i in range(num_blks):
                size, offset = self._read_uint32(mm, offset)
                self.blk_sizes.append(size)

            return offset
        # Extended symlink
        elif self.inode_type == 10:
            # TODO
            raise SquashError

        # Extended blk device
        elif self.inode_type == 11:
            # TODO
            raise SquashError

        # Extended char device
        elif self.inode_type == 12:
            # TODO
            raise SquashError

        # Extended fifo
        elif self.inode_type == 13:
            # TODO
            raise SquashError

        # Extended socket
        elif self.inode_type == 14:
            # TODO
            raise SquashError

        # Unknown inode type
        else:
            raise SquashError
