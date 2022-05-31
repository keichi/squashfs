from typing import Dict, TYPE_CHECKING

from .common import Mixin
if TYPE_CHECKING:
    from .image import Image
    from .inode import Inode


class Info(Mixin):
    def __init__(self, image: "Image", inode: "Inode") -> None:
        self.image = image
        self.inode = inode

    @property
    def size(self) -> int:
        return self.inode.file_size

    @property
    def permissions(self) -> int:
        return self.inode.permissions

    @property
    def uid(self) -> int:
        return self.image.ids[self.inode.uid_idx]

    @property
    def gid(self) -> int:
        return self.image.ids[self.inode.gid_idx]

    @property
    def modified_time(self) -> int:
        return self.inode.modified_time

    @property
    def xattrs(self) -> Dict[bytes, bytes]:
        if self.inode.xattr_idx == 0xffffffff:
            return {}
        return self.image.xattrs[self.inode.xattr_idx]

    @property
    def is_dir(self) -> bool:
        return self.inode.is_dir

    @property
    def is_symlink(self) -> bool:
        return self.inode.is_symlink

    @property
    def is_file(self) -> bool:
        return self.inode.is_file

    @property
    def is_block_dev(self) -> bool:
        return self.inode.is_block_dev

    @property
    def is_char_dev(self) -> bool:
        return self.inode.is_char_dev

    @property
    def is_fifo(self) -> bool:
        return self.inode.is_fifo

    @property
    def is_socket(self) -> bool:
        return self.inode.is_socket


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(size={self.size}, permissions=0o{self.permissions:o}, uid={self.uid}, gid={self.gid}, modified_time={self.modified_time}, xattrs={self.xattrs})"
