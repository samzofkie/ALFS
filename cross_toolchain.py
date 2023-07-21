import os, shutil, subprocess
from phase import PreChrootPhase


class CrossToolchainBuild(PreChrootPhase):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)

        self.targets["cross_binutils"] = {
            "build_commands": [
                (
                    f"../configure --prefix={self.root_dir}/tools "
                    f"--with-sysroot={self.root_dir} "
                    f"--target={self.lfs_triplet} --disable-nls --enable-gprofng=no "
                    "--disable-werror"
                ),
                "make",
                "make install",
            ],
            "build_dir": True,
        }

        self.targets["cross_gcc"] = {
            "build_commands": [
                (
                    f"../configure --target={self.lfs_triplet} --prefix={self.root_dir}/tools "
                    f"--with-glibc-version=2.37 --with-sysroot={self.root_dir} --with-newlib "
                    "--without-headers --enable-default-pie --enable-default-ssp "
                    "--disable-nls --disable-shared --disable-multilib --disable-threads "
                    "--disable-libatomic --disable-libgomp --disable-libquadmath "
                    "--disable-libssp --disable-libvtv --disable-libstdcxx "
                    "--enable-languages=c,c++"
                ),
                "make",
                "make install",
            ],
            "build_dir": True,
        }

        self.targets["linux_headers"] = {
            "build_commands": ["make mrproper", "make headers"],
            "search_term": "linux",
        }

        self.targets["cross_glibc"] = {
            "build_commands": [
                (
                    f"../configure --prefix=/usr --host={self.lfs_triplet} --build={self.host_triplet} "
                    f"--enable-kernel=3.2 --with-headers={self.root_dir}/usr/include "
                    "libc_cv_slibdir=/usr/lib"
                ),
                "make",
                f"make DESTDIR={self.root_dir} install",
            ],
            "build_dir": True,
        }

        self.targets["cross_libstdcpp"] = {
            "build_commands": [
                (
                    f"../libstdc++-v3/configure --host={self.lfs_triplet} --build={self.host_triplet} "
                    "--prefix=/usr --disable-multilib --disable-nls "
                    "--disable-libstdcxx-pch "
                    f"--with-gxx-include-dir=/tools/{self.lfs_triplet}/include/c++/12.2.0"
                ),
                "make",
                f"make DESTDIR={self.root_dir} install",
            ],
            "search_term": "gcc",
            "build_dir": True,
        }

    def _cross_gcc_before(self):
        self._common_gcc_before()

    def _cross_gcc_after(self):
        os.chdir("..")
        lines = []
        for file in ["gcc/limitx.h", "gcc/glimits.h", "gcc/limity.h"]:
            with open(file, "r") as f:
                lines += f.readlines()
        completed = subprocess.run(
            f"{self.lfs_triplet}-gcc -print-libgcc-file-name".split(" "),
            capture_output=True,
            env=self.env,
            check=True,
        )
        dirname = completed.stdout.decode().rsplit("/", 1)[0]
        with open(dirname + "/install-tools/include/limits.h", "w") as f:
            f.writelines(lines)

    def _linux_headers_after(self):
        for root, dirs, files in os.walk("usr/include"):
            for file in files:
                if file[-2:] != ".h":
                    os.remove(f"{root}/{file}")
        if not os.path.exists(f"{self.root_dir}/usr/include"):
            os.mkdir(f"{self.root_dir}/usr/include")
        shutil.copytree("usr/include", f"{self.root_dir}/usr/include",
                        dirs_exist_ok=True)
            
    def _cross_glibc_before(self):
        os.symlink(
            "../usr/lib/ld-linux-x86-64.so.2",
            self.root_dir + "/lib64/ld-linux-x86-64.so.2",
        )
        os.symlink(
            "../usr/lib/ld-linux-x86-64.so.2",
            self.root_dir + "/lib64/ld-lsb-x86-64.so.3",
        )
        package_name = self._package_name_from_tarball(
            self._search_for_tarball("glibc")
        )
        self._run(f"patch -Np1 -i {self.root_dir}/sources/{package_name}-fhs-1.patch")

        if not os.path.exists("build"):
            os.mkdir("build")
        with open("build/configparms", "w") as f:
            f.write("rootsbindir=/usr/sbin")

    def _cross_glibc_after(self):
        with open("main.c", "w") as f:
            f.write("int main(){}")
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

    def _cross_libstdcpp_after(self):
        for prefix in ["stdc++", "stdc++fs", "supc++"]:
            archive = self.root_dir + "/usr/lib/lib" + prefix + ".la"
            if os.path.exists(archive):
                os.remove(archive)
