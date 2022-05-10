from squashfs.image import Image


def test_basic():
    with Image("tests/test_basic.sfs") as image:
        assert image.listdir("") == [
            "001_directory",
            "002_file",
            "003_symlink",
            "004_block_dev",
            "005_char_dev",
            "006_fifo",
            "007_socket",
        ]


def test_xattrs():
    with Image("tests/test_xattr.sfs") as image:

        assert image.open("foo").xattrs == {
            b"security.capability": b"\x01\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00",
            b"user.shatag.sha256": b"634b027b1b69e1242d40d53e312b3b4ac7710f55be81f289b549446ef6778bee",
        }

        assert image.open("bar").xattrs == {
            b"user.shatag.sha256": b"7d6fd7774f0d87624da6dcf16d0d3d104c3191e771fbe2f39c86aed4b2bf1a0f"
        }
