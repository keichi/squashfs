import mmap
import sys

from .image import Image


def main():
    with open(sys.argv[1], "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        image = Image(mm)


if __name__ == "__main__":
    main()
