import os, subprocess, shutil, time
import utils


class Package:
    def __init__(self, file_tracker):
        self.file_tracker = file_tracker

    def root_dir(self):
        return self.file_tracker.root_dir

    def tarball_name(self):
        return self.tarball_url.split("/")[-1]

    def package_name(self):
        return self.tarball_name().split(".tar")[0]

    def name(self):
        return self.__class__.__name__

    def _untar_and_enter_source_tree(self):
        os.chdir(self.root_dir())
        print(f"unpacking {self.package_name()}")
        subprocess.run(
            f"tar -xvf sources/{self.tarball_name()}".split(" "),
            check=True,
            capture_output=True,
        )
        os.chdir(self.package_name())

    @staticmethod
    def create_and_enter_build_dir():
        utils.ensure_dir("build")
        os.chdir("build")

    def build(self):
        if not self.file_tracker.record_exists(self.name()):
            self._untar_and_enter_source_tree()
            start_time = time.time()
            self._inner_build()
            os.chdir(self.root_dir())
            utils.ensure_removal(self.package_name())
            self.file_tracker.record_new_files_since(start_time, self.name())

    def apply_patch(self):
        utils.run(
            "patch -Np1 -i "
            f"{self.root_dir()}/sources/{self.patch_url.split('/')[-1]}"
        )


def gcc_change_default_64_bit_dir():
    shutil.copyfile("gcc/config/i386/t-linux64", "gcc/config/i386/t-linux64.orig")
    utils.modify(
        "gcc/config/i386/t-linux64",
        lambda line, _: line.replace("lib64", "lib") if "m64" in line else line,
    )


class PreChrootPackage(Package):
    def __init__(self, file_tracker):
        super().__init__(file_tracker)
        self.lfs_triplet = "x86_64-lfs-linux-gnu"
        self.host_triplet = "x86_64-pc-linux-gnu"
        self.config_prefix_host = f"./configure --prefix=/usr --host={self.lfs_triplet}"
        self.config_prefix_host_build = (
            self.config_prefix_host + f" --build={self.host_triplet}"
        )
        self.make_destdir = ["make", f"make DESTDIR={self.root_dir()} install"]

    def _common_gcc_before(self):
        for tarball in os.listdir(f"{self.root_dir()}/sources"):
            for name in ["mpfr", "gmp", "mpc"]:
                if name in tarball:
                    subprocess.run(
                        f"tar -xvf " f"{self.root_dir()}/sources/{tarball}".split(),
                        check=True,
                        capture_output=True,
                    )
                    os.rename(tarball.split(".tar")[0], name)
        gcc_change_default_64_bit_dir()
