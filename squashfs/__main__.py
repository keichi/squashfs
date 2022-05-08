import datetime
import sys

from .image import Image


def main():
    with Image(sys.argv[1]) as image:
        f = image.open(sys.argv[2])

        print("Size:", f.size)
        print("Permission:", oct(f.permissions))
        print("UID:", f.uid)
        print("GID:", f.gid)
        print("Modtime:", datetime.datetime.fromtimestamp(f.modified_time))


if __name__ == "__main__":
    main()
