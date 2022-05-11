from .common import Mixin


class Info(Mixin):
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

    @property
    def xattrs(self):
        if self.inode.xattr_idx == 0xffffffff:
            return {}
        return self.image.xattrs[self.inode.xattr_idx]

    @property
    def is_dir(self):
        return self.inode.is_dir

    @property
    def is_symlink(self):
        return self.inode.is_symlink

    @property
    def is_file(self):
        return self.inode.is_file

    @property
    def is_block_dev(self):
        return self.inode.is_block_dev

    @property
    def is_char_dev(self):
        return self.inode.is_char_dev

    @property
    def is_fifo(self):
        return self.inode.is_fifo

    @property
    def is_socket(self):
        return self.inode.is_socket


    def __repr__(self):
        return f"{self.__class__.__name__}(size={self.size}, permissions=0o{self.permissions:o}, uid={self.uid}, gid={self.gid}, modified_time={self.modified_time}, xattrs={self.xattrs})"
