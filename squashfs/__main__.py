import mmap
import os
import sys

from .image import Image


def main():
    with open(sys.argv[1], "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        image = Image(mm)

        f = image.open("/etc/group")

        os.write(sys.stdout.fileno(), f.read())


if __name__ == "__main__":
    main()
