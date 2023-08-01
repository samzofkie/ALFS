import unittest
import os
import shutil

import utils


class SeparateDirBase(unittest.TestCase):
    def setUp(self):
        self.start_dir = os.getcwd()
        os.mkdir("test")
        os.chdir("test")

    def tearDown(self):
        os.chdir(self.start_dir)
        shutil.rmtree("test")


class TestReadFile(SeparateDirBase):
    def test_read_file(self):
        test_lines = ["a\n", "b\n", "c\n"]
        with open("test", "w") as f:
            f.writelines(test_lines)
        self.assertEqual(test_lines, utils.read_file("test"))
        os.remove("test")


class TestWriteFile(SeparateDirBase):
    def test_write_file(self):
        test_lines = ["whatever\n"] * 3
        utils.write_file("test", test_lines)
        with open("test", "r") as f:
            lines = f.readlines()
        self.assertEqual(lines, test_lines)
        os.remove("test")

    def test_empty_file(self):
        utils.write_file("test", [])
        with open("test", "r") as f:
            self.assertEqual([], f.readlines())
        self.assertTrue("test" in os.listdir())


class TestEnsureDir(SeparateDirBase):
    def _check_abc_hierarchy(self):
        self.assertTrue(os.path.isdir("a"))
        self.assertTrue(os.path.isdir("a/b"))
        self.assertTrue(os.path.isdir("a/b/c"))

    def test_ensure_dir_simple_create(self):
        utils.ensure_dir("a")
        self.assertTrue(os.path.isdir("a"))
        shutil.rmtree("a")

    def test_ensure_dir_multiple_levels(self):
        utils.ensure_dir("a/b/c")
        self._check_abc_hierarchy()
        shutil.rmtree("a")

    def test_ensure_dir_exists(self):
        os.mkdir("a")
        utils.ensure_dir("a")
        self.assertTrue(os.path.isdir("a"))

    def test_ensure_dir_multiple_levels_exists(self):
        os.makedirs("a/b/c")
        utils.ensure_dir("a/b/c")
        self._check_abc_hierarchy()

    def test_ensure_dir_multiple_levels_exists_extra(self):
        os.makedirs("a/b/c")
        utils.ensure_dir("a/b/c/d")
        self._check_abc_hierarchy()
        self.assertTrue(os.path.isdir("a/b/c/d"))


class TestEnsureSymlink(SeparateDirBase):
    @staticmethod
    def _touch_a():
        with open("a", "w") as f:
            pass

    def test_new_link(self):
        self._touch_a()
        utils.ensure_symlink("a", "b")
        self.assertTrue(os.path.islink("b"))
        os.remove("a")

    def test_link_exists(self):
        self._touch_a()
        os.symlink("a", "b")
        utils.ensure_symlink("a", "b")
        self.assertTrue(os.path.islink("b"))
        os.remove("a")

    def test_pointed_at_doesnt_exist(self):
        utils.ensure_symlink("a", "b")
        self.assertTrue(os.path.islink("b"))


class TestEnsureTouch(SeparateDirBase):
    def test_touch(self):
        utils.ensure_touch("a")
        self.assertTrue("a" in os.listdir())

    def test_already_exists(self):
        content = ["ok\n", "no problemo\n"]
        with open("a", "w") as f:
            f.writelines(content)
        utils.ensure_touch("a")
        self.assertTrue("a" in os.listdir())
        with open("a", "r") as f:
            self.assertTrue(f.readlines() == content)

    def test_path(self):
        os.makedirs("a/b/c")
        utils.ensure_touch("a/b/c/d")
        self.assertTrue(os.path.exists("a/b/c/d"))
        shutil.rmtree("a")


class TestEnsureRemoval(SeparateDirBase):
    def test_no_file(self):
        utils.ensure_removal("a")

    def test_normal_file(self):
        utils.ensure_touch("a")
        utils.ensure_removal("a")
        self.assertTrue("a" not in os.listdir())

    def test_dir(self):
        os.mkdir("a")
        utils.ensure_removal("a")
        self.assertTrue("a" not in os.listdir())

    def test_full_dir(self):
        os.mkdir("a")
        for file in ["b", "c", "d"]:
            utils.ensure_touch(f"a/{file}")
        utils.ensure_removal("a")
        self.assertTrue("a" not in os.listdir())

    def test_symlink(self):
        os.symlink("a", "b")
        utils.ensure_removal("b")
        self.assertTrue("b" not in os.listdir())


class TestModify(SeparateDirBase):
    def test_empty_file(self):
        utils.ensure_touch("a")
        utils.modify("a", lambda line, i: line if "a" not in line else "b")
        self.assertTrue(utils.read_file("a") == [])

    def test_a_to_b(self):
        content = ["a\n", "aa\n", "ab\n", "b\n"]
        utils.write_file("a", content)
        utils.modify("a", lambda line, _: line.replace("a", "b"))
        content = [line.replace("a", "b") for line in content]
        self.assertTrue(utils.read_file("a") == content)

    def test_only_one_line(self):
        content = ["a\n", "aa\n", "ab\n", "b\n"]
        utils.write_file("a", content)
        utils.modify("a", lambda line, i: line.replace("a", "b") if i == 2 else line)
        content[2] = content[2].replace("a", "b")
        self.assertTrue(utils.read_file("a") == content)


if __name__ == "__main__":
    unittest.main()
