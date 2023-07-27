import unittest
import os
import shutil

import utils

class SeperateDirBase(unittest.TestCase):
    def setUp(self):
        self.start_dir = os.getcwd()
        os.mkdir("test")
        os.chdir("test")

    def tearDown(self):
        os.chdir(self.start_dir)
        shutil.rmtree("test")


class TestReadFile(SeperateDirBase):
    def test_read_file(self):
        test_lines = ["a\n", "b\n", "c\n"]
        with open("test", "w") as f:
            f.writelines(test_lines)
        self.assertEqual(test_lines, utils.read_file("test"))
        os.remove("test")


class TestWriteFile(SeperateDirBase):
    def test_write_file(self):
        test_lines = ["whatever\n"] * 3
        utils.write_file("test", test_lines)
        with open("test", "r") as f:
            lines = f.readlines()
        self.assertEqual(lines, test_lines)
        os.remove("test")


class TestEnsureDir(SeperateDirBase):
    def test_ensure_dir_simple_create(self):
        utils.ensure_dir("a")
        self.assertTrue(os.path.isdir("a"))
        shutil.rmtree("a")

    def test_ensure_dir_multiple_levels(self):
        utils.ensure_dir("a/b/c")
        self.assertTrue(os.path.isdir("a"))
        self.assertTrue(os.path.isdir("a/b"))
        self.assertTrue(os.path.isdir("a/b/c"))
        shutil.rmtree("a")

    def test_ensure_dir_exists(self):
        os.mkdir("a")
        utils.ensure_dir("a")
        self.assertTrue(os.path.isdir("a"))

    def test_ensure_dir_multiple_levels_exists(self):
        os.makedirs("a/b/c")
        utils.ensure_dir("a/b/c")
        self.assertTrue(os.path.isdir("a"))
        self.assertTrue(os.path.isdir("a/b"))
        self.assertTrue(os.path.isdir("a/b/c"))

    def test_ensure_dir_multiple_levels_exists_extra(self):
        os.makedirs("a/b/c")
        utils.ensure_dir("a/b/c/d")
        self.assertTrue(os.path.isdir("a"))
        self.assertTrue(os.path.isdir("a/b"))
        self.assertTrue(os.path.isdir("a/b/c"))
        self.assertTrue(os.path.isdir("a/b/c/d"))


if __name__ == "__main__":
    unittest.main()
