import hashlib

from squashfs.image import Image


def test_inode_types():
    DIGESTS = {
        "128k": "ad9ceb1109d6f89d26ea6bd6bb04c3aee487847f",
        "129k": "d89d33c0a206db9c4541c913136cacb3e15b4a1b",
        "256k": "a07988abd80b105a79c67ccef59c55f264854b66",
        "4k": "5381f594537fb26e45c5924d4bf1e3d9b54e52bb"
    }

    with Image("tests/test_file.sfs") as image:
        for file in image.listdir():
            data = image.open(file)

            assert hashlib.sha1(data).hexdigest() == DIGESTS[file]
