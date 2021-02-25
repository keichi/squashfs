import datetime
import mmap
#  import os
import sys

from .image import Image


def main():
    with open(sys.argv[1], "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        image = Image(mm)

        f = image.open(sys.argv[2])

        print("Size:", f.size)
        print("Permission:", oct(f.permissions))
        print("UID:", f.uid)
        print("GID:", f.gid)
        print("Modtime:", datetime.datetime.fromtimestamp(f.modified_time))

        #  os.write(sys.stdout.fileno(), f.read())


if __name__ == "__main__":
    main()
