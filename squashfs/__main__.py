import mmap
import sys

from .image import Image


def main():
    with open(sys.argv[1], "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        image = Image(mm)

        f = image.open("/etc/passwd")

        print(f.inode.blk_start)
        print(f.inode.fragment_blk_index)
        print(f.inode.blk_offset)
        print(f.inode.file_size)
        print(f.inode.blk_sizes)


if __name__ == "__main__":
    main()
