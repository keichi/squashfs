import datetime
import sys

from .image import Image


def main() -> None:
    with Image(sys.argv[1]) as image:
        f = image.open(sys.argv[2])

        print("Size:", f.size)
        print("Permission:", oct(f.permissions))
        print("UID:", f.uid)
        print("GID:", f.gid)
        print("Modtime:", datetime.datetime.fromtimestamp(f.modified_time))
        print("Xattrs:", f.xattrs)


if __name__ == "__main__":
    main()
