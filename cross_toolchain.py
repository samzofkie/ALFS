import os, shutil, subprocess
from phase import Phase

LFS_TGT = "x86_64-lfs-linux-gnu"
HOST_TRIPLET = "x86_64-pc-linux-gnu"


class CrossToolchainBuild(Phase):
    def __init__(self, root_dir, ft):
        super().__init__(root_dir, ft)
        self.env = { 
            "LC_ALL": "POSIX", 
            "PATH": f"{self.root_dir}/tools/bin:/usr/bin",
            "CONFIG_SITE": f"{self.root_dir}/usr/share/config.site" 
        }

        """self.targets["cross_binutils"] = {
            "build_commands": [
                (f"../configure --prefix={self.root_dir}/tools "
                f"--with-sysroot={self.root_dir} "
                f"--target={LFS_TGT} --disable-nls --enable-gprofng=no "
                "--disable-werror"),
                "make", 
                "make install"
            ],
            "build_dir": True
        }"""

        """self.targets["cross_gcc"] = {
            "build_commands": [
                (f"../configure --target={LFS_TGT} --prefix={self.root_dir}/tools "
                f"--with-glibc-version=2.37 --with-sysroot={self.root_dir} --with-newlib "
                "--without-headers --enable-default-pie --enable-default-ssp "
                "--disable-nls --disable-shared --disable-multilib --disable-threads "
                "--disable-libatomic --disable-libgomp --disable-libquadmath "
                "--disable-libssp --disable-libvtv --disable-libstdcxx "
                "--enable-languages=c,c++"),
                "make",
                "make install"
            ],
            "build_dir": True
        }

        self.targets["linux_headers"] = {
                "build_commands": ["make mrproper", "make headers"],
                "search_term": "linux"
        }"""

        self.targets["cross_glibc"] = {
            "build_commands": [
                (f"../configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET} "
                f"--enable-kernel=3.2 --with-headers={self.root_dir}/usr/include "
                "libc_cv_slibdir=/usr/lib"),
                "make", 
                f"make DESTDIR={self.root_dir} install"
            ],
            "build_dir": True
        }

        self.targets["cross_libstdcpp"] = {
            "build_commands": [
                (f"../libstdc++-v3/configure --host={LFS_TGT} --build={HOST_TRIPLET} "
                "--prefix=/usr --disable-multilib --disable-nls "
                "--disable-libstdcxx-pch "
                f"--with-gxx-include-dir=/tools/{LFS_TGT}/include/c++/12.2.0"),
                "make",
                f"make DESTDIR={self.root_dir} install"
            ],
            "search_term": "gcc",
            "build_dir": True
        }


    def _cross_gcc_before(self):
        for dep in ["mpfr", "gmp", "mpc"]:
            tarball_name = self._search_for_tarball(dep)
            package_name = self._package_name_from_tarball(tarball_name)
            subprocess.run(f"tar -xvf "
                           f"{self.root_dir}/sources/{tarball_name}".split(),
                           check=True, capture_output=True)
            self._run(f"mv {package_name} {dep}")

        shutil.copyfile("gcc/config/i386/t-linux64", 
                        "gcc/config/i386/t-linux64.orig")
        with open("gcc/config/i386/t-linux64", "r") as f:
            lines = f.readlines()
        for line in lines:
            if "m64=" in line:
                line = line.replace("lib64", "lib")
        with open("gcc/config/i386/t-linux64", "w") as f:
            f.writelines(lines)


    def _cross_gcc_after(self):
        os.chdir("..")
        lines = []
        for file in ["gcc/limitx.h", "gcc/glimits.h", "gcc/limity.h"]:
            with open(file, "r") as f:
                lines += f.readlines()
        completed = subprocess.run(
            f"{LFS_TGT}-gcc -print-libgcc-file-name".split(" "),
            capture_output=True, env=self.env, check=True)
        dirname = completed.stdout.decode().rsplit("/",1)[0]
        with open (dirname + "/install-tools/include/limits.h", "w") as f:
            f.writelines(lines)


    def _linux_headers_after(self):
        destination = self.root_dir
        files = ["usr/include"]
        while files:
            curr = files.pop()
            if os.path.isdir(curr):
                files += [curr + "/" + f for f in os.listdir(curr)]
                os.mkdir(destination + "/" + curr)
            elif curr[-2:] == ".h":
                shutil.copy(curr, destination + "/" + curr)


    def _cross_glibc_before(self):
        os.symlink("../usr/lib/ld-linux-x86-64.so.2", self.root_dir +
                   "/lib64/ld-linux-x86-64.so.2")
        os.symlink("../usr/lib/ld-linux-x86-64.so.2", self.root_dir + 
                   "/lib64/ld-lsb-x86-64.so.3")
        package_name = self._package_name_from_tarball(
                self._search_for_tarball("glibc"))
        self._run(f"patch -Np1 -i {self.root_dir}/sources/{package_name}-fhs-1.patch")
        
        if not os.path.exists("build"):
            os.mkdir("build")
        with open("build/configparms", "w") as f:
            f.write("rootsbindir=/usr/sbin")


    def _cross_glibc_after(self):
        with open("main.c", "w") as f:
            f.write("int main(){}")
        self._run(f"{LFS_TGT}-gcc -xc main.c")
        completed_process = subprocess.run("readelf -l a.out".split(" "),
                                           env=self.env, check=True,
                                           capture_output=True)
        assert ( "[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]" 
                in completed_process.stdout.decode() )
        self._run(f"{self.root_dir}/tools/libexec/gcc/{LFS_TGT}/12.2.0/"
                  "install-tools/mkheaders") 


    def _cross_libstdcpp_after(self):
        for prefix in ["stdc++", "stdc++fs", "supc++"]:
            archive = self.root_dir + "/usr/lib/lib" + prefix + ".la"
            if os.path.exists(archive):
                os.remove(archive)
