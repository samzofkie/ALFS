import unittest
import os
import shutil
from alfs import Alfs

class TestAlfsSetup(unittest.TestCase):
    def setUp(self):
        self.home = os.getcwd()
        os.mkdir("test")
        os.chdir("test")
        self.test_dir = self.home + "/test"
        self.alfs = Alfs()

    def tearDown(self):
        os.chdir(self.home)
        shutil.rmtree("test")

    def test_root_dir(self):
        self.assertEqual(self.test_dir, self.alfs.root_dir)

    def test_ensure_wget_list(self):
        if "wget-list" in os.listdir():
            os.remove("wget-list")
        self.alfs.ensure_wget_list()
        self.assertTrue("wget-list" in os.listdir())

    def test_ensure_directory_skeletion(self):
        files = set(os.listdir())
        self.alfs.ensure_directory_skeleton()
        new_files = list(set(os.listdir()) - files) + ["sources"]
        root_level = [dir for dir in self.alfs.system_dirs if "/" not in dir]
        self.assertEqual(new_files.sort(), root_level.sort())


class TestAlfsCopyAllHeaders(unittest.TestCase):
    def setUp(self):
        self.home = os.getcwd()
        os.mkdir("test")
        os.chdir("test")
        self.test_dir = os.getcwd()
        os.mkdir("a")
        def touch(file_path):
            with open(file_path, "w") as f:
                f.writelines(["file"])
        touch("a/b")
        touch("a/c.h")
        os.mkdir("a/d")
        touch("a/d/e")
        touch("a/d/f.h")

    def tearDown(self):
        os.chdir(self.test_dir)
        shutil.rmtree("a")
        os.chdir(self.home)
        shutil.rmtree("test")

    def test_copy_all_headers(self):
        Alfs.copy_all_headers("a","aa")
        self.assertTrue(os.path.exists("aa/a"))
        self.assertTrue(os.path.exists("aa/a/c.h"))
        self.assertTrue(os.path.exists("aa/a/d/f.h"))



if __name__ == '__main__':
    unittest.main()

