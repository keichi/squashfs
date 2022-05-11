from squashfs.image import Image


def test_xattrs():
    with Image("tests/test_xattr.sfs") as image:
        assert image.stat("foo").xattrs == {
            b"security.capability": b"\x01\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00",
            b"user.shatag.sha256": b"634b027b1b69e1242d40d53e312b3b4ac7710f55be81f289b549446ef6778bee",
        }

        assert image.stat("bar").xattrs == {
            b"user.shatag.sha256": b"7d6fd7774f0d87624da6dcf16d0d3d104c3191e771fbe2f39c86aed4b2bf1a0f"
        }

def test_xattrs2():
    with Image("tests/test_xattr2.sfs") as image:
        j = 0

        for i in range(8):
            xattrs = image.stat(f"baz{i}").xattrs

            for _ in range(16):
                t = bytes(str(j), "utf8")
                assert xattrs[b"user.key" + t] == b"v" * 128 + t
                j += 1
