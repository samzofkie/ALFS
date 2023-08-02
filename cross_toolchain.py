import os, shutil, subprocess

from package import PreChrootPackage
import utils


class CrossBinutils(PreChrootPackage):
    def _inner_build(self):
        self._create_and_enter_build_dir()
        self._run_commands(
            [
                f"../configure --prefix={self.root_dir}/tools "
                f"--with-sysroot={self.root_dir} "
                f"--target={self.lfs_triplet} --disable-nls --enable-gprofng=no "
                "--disable-werror",
                "make",
                "make install",
            ]
        )


class CrossGcc(PreChrootPackage):
    def _inner_build(self):
        self._common_gcc_before()
        self._create_and_enter_build_dir()
        self._run_commands(
            [
                f"../configure --target={self.lfs_triplet} --prefix={self.root_dir}/tools "
                f"--with-glibc-version=2.37 --with-sysroot={self.root_dir} --with-newlib "
                "--without-headers --enable-default-pie --enable-default-ssp "
                "--disable-nls --disable-shared --disable-multilib --disable-threads "
                "--disable-libatomic --disable-libgomp --disable-libquadmath "
                "--disable-libssp --disable-libvtv --disable-libstdcxx "
                "--enable-languages=c,c++",
                "make",
                "make install",
            ]
        )

        os.chdir("..")
        lines = []
        for file in ["gcc/limitx.h", "gcc/glimits.h", "gcc/limity.h"]:
            lines += utils.read_file(file)
        completed = subprocess.run(
            f"{self.lfs_triplet}-gcc -print-libgcc-file-name".split(" "),
            capture_output=True,
            env=self.env,
            check=True,
        )
        dirname = completed.stdout.decode().rsplit("/", 1)[0]
        utils.write_file(f"{dirname}/install-tools/include/limits.h", lines)


class LinuxHeaders(PreChrootPackage):
    def __init__(self, root, file_tracker):
        super().__init__(root, file_tracker)
        self.search_term = "linux"

    def _inner_build(self):
        self._run_commands(["make mrproper", "make headers"])
        for root, dirs, files in os.walk("usr/include"):
            for file in files:
                if file[-2:] != ".h":
                    utils.ensure_removal(f"{root}/{file}")
        utils.ensure_dir(f"{self.root_dir}/usr/include")
        shutil.copytree(
            "usr/include", f"{self.root_dir}/usr/include", dirs_exist_ok=True
        )


class CrossGlibc(PreChrootPackage):
    def _inner_build(self):
        utils.ensure_symlink(
            "../usr/lib/ld-linux-x86-64.so.2",
            f"{self.root_dir}/lib64/ld-linux-x86-64.so.2",
        )
        utils.ensure_symlink(
            "../usr/lib/ld-linux-x86-64.so.2",
            f"{self.root_dir}/lib64/ld-lsb-x86-64.so.3",
        )
        package_name = self._package_name_from_tarball(
            self._search_for_tarball("glibc")
        )
        self._run(f"patch -Np1 -i {self.root_dir}/sources/{package_name}-fhs-1.patch")
        utils.ensure_dir("build")
        utils.write_file("build/configparms", ["rootsbindir=/usr/sbin"])

        self._create_and_enter_build_dir()
        self._run_commands(
            [
                f"../configure --prefix=/usr --host={self.lfs_triplet} --build={self.host_triplet} "
                f"--enable-kernel=3.2 --with-headers={self.root_dir}/usr/include "
                "libc_cv_slibdir=/usr/lib",
                "make",
                f"make DESTDIR={self.root_dir} install",
            ]
        )

        utils.write_file("main.c", "int main(){}")
        self._run(f"{self.lfs_triplet}-gcc -xc main.c")
        completed_process = subprocess.run(
            "readelf -l a.out".split(" "), env=self.env, check=True, capture_output=True
        )
        assert (
            "[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]"
            in completed_process.stdout.decode()
        )
        self._run(
            f"{self.root_dir}/tools/libexec/gcc/{self.lfs_triplet}/12.2.0/"
            "install-tools/mkheaders"
        )


class CrossLibstdcpp(PreChrootPackage):
    def __init__(self, root, file_tracker):
        super().__init__(root, file_tracker)
        self.search_term = "gcc"

    def _inner_build(self):
        self._create_and_enter_build_dir()
        self._run_commands(
            [
                f"../libstdc++-v3/configure --host={self.lfs_triplet} "
                f"--build={self.host_triplet} --prefix=/usr --disable-multilib "
                "--disable-nls --disable-libstdcxx-pch "
                f"--with-gxx-include-dir=/tools/{self.lfs_triplet}/include/c++/12.2.0",
                "make",
                f"make DESTDIR={self.root_dir} install",
            ]
        )
        for name in ["stdc++", "stdc++fs", "supc++"]:
            utils.ensure_removal(f"{self.root_dir}/usr/lib/lib{name}.la")


cross_toolchain_packages = [
    CrossBinutils,
    CrossGcc,
    LinuxHeaders,
    CrossGlibc,
    CrossLibstdcpp,
]

