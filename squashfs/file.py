import zlib

from .common import Mixin


class File(Mixin):
    def __init__(self, image, inode):
        self.image = image
        self.inode = inode

    @property
    def size(self):
        return self.inode.file_size

    @property
    def permissions(self):
        return self.inode.permissions

    @property
    def uid(self):
        return self.image.ids[self.inode.uid_idx]

    @property
    def gid(self):
        return self.image.ids[self.inode.gid_idx]

    @property
    def modified_time(self):
        return self.inode.modified_time

    def read(self):
        buffer = b""

        offset = self.inode.blks_start

        for size in self.inode.blk_sizes:
            buffer += zlib.decompress(self.image.mm[offset:offset+size])
            offset += size

        # File contains a fragment
        frag_idx = self.inode.fragment_blk_index
        if frag_idx != 0xffffffff:
            start = self.image.fragments[frag_idx].start
            size = self.image.fragments[frag_idx].size
            fragment = zlib.decompress(self.image.mm[start:start+size])
            frag_offset = self.inode.blk_offset
            frag_size = self.inode.file_size % self.image.sblk.blk_size

            buffer += fragment[frag_offset:frag_offset+frag_size]

        return buffer
