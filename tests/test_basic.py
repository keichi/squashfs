from squashfs.image import Image


def test_inode_types():
    with Image("tests/test_basic.sfs") as image:
        assert image.listdir() == [
            "001_directory",
            "002_file",
            "003_symlink",
            "004_block_dev",
            "005_char_dev",
            "006_fifo",
            "007_socket",
        ]

        info = image.stat("001_directory")
        assert info.permissions == 0o775
        assert info.is_dir
        assert info.uid == 1000
        assert info.gid == 1000

        info = image.stat("002_file")
        assert info.permissions == 0o664
        assert info.is_file
        assert info.uid == 1000
        assert info.gid == 1000

        info = image.stat("003_symlink")
        assert info.permissions == 0o777
        assert info.is_symlink
        assert info.uid == 1000
        assert info.gid == 1000

        info = image.stat("004_block_dev")
        assert info.permissions == 0o644
        assert info.is_block_dev
        assert info.uid == 0
        assert info.gid == 0

        info = image.stat("005_char_dev")
        assert info.permissions == 0o644
        assert info.is_char_dev
        assert info.uid == 0
        assert info.gid == 0

        info = image.stat("006_fifo")
        assert info.permissions == 0o664
        assert info.is_fifo
        assert info.uid == 1000
        assert info.gid == 1000

        info = image.stat("007_socket")
        assert info.permissions == 0o775
        assert info.is_socket
        assert info.uid == 1000
        assert info.gid == 1000
