#!/usr/bin/env python3

import os
from urllib.request import urlopen
import subprocess
import shutil


class Alfs:
    lfs_tgt = "x86_64-lfs-linux-gnu"
    system_dirs = ["etc", "var", "usr/bin", "usr/lib", "usr/sbin", 
                   "lib64", "tools"]

    def __init__(self):
        self.root_dir = os.getcwd()
        self.env_vars = { 
            "LC_ALL": "POSIX", 
            "PATH": f"{self.root_dir}/tools/bin:/usr/bin",
            "CONFIG_SITE": f"{self.root_dir}/usr/share/config.site" 
        }
        self.ensure_wget_list()
        self.ensure_directory_skeleton()
        self.ensure_tarballs_downloaded()
        self.all_files = self.system_snapshot()


    def ensure_wget_list(self):
        os.chdir(self.root_dir)
        if not os.path.exists("wget-list"):
            res = urlopen("https://www.linuxfromscratch.org/lfs/" \
                "downloads/stable/wget-list")
            with open("wget-list", "w") as f:
                f.writelines(res.read().decode())


    def ensure_directory_skeleton(self):
        os.chdir(self.root_dir)
        for dir in self.system_dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)
        if not os.path.exists("sources"):
            os.mkdir("sources")


    def ensure_tarballs_downloaded(self):
        os.chdir(self.root_dir)
        with open("wget-list", "r") as f:
            tarball_urls = [line.split("\n")[0] for line in f.readlines()]

        for url in tarball_urls:
            tarball_name = url.split("/")[-1]
            if not os.path.exists("sources/" + tarball_name): 
                print("downloading " + tarball_name + "...")
                res = urlopen(url)
                with open("sources/" + tarball_name, "wb") as f:
                    f.write(res.read())


    def system_snapshot(self):
        os.chdir(self.root_dir)
        dirs = self.system_dirs.copy()
        all_files = set()
        while dirs:
            curr = dirs.pop()
            for file in os.listdir(curr):
                full_path = curr + "/" + file
                if os.path.isdir(full_path):
                    dirs.append(full_path)
                else:
                    all_files.add(full_path)
        return all_files


    class TarballNotFoundError(Exception):
        pass

    def get_tarball_name(self, package_name):
        tarballs = os.listdir(f"{self.root_dir}/sources")
        res = [tarball for tarball in tarballs if package_name in tarball]
        res = [tarball for tarball in res if ".patch" not in tarball]
        if len(res) < 1:
            raise TarballNotFoundError("No results from search term \"" +
                                       package_name + "\"")
        elif len(res) > 1:
            raise TarballNotFoundError("Too many results from search term \"" +
                                    package_name + "\": " + str(res))
        return res[0]


    def untar_and_enter_source_dir(self, package_name):
        os.chdir(self.root_dir)
        tarball_name = self.get_tarball_name(package_name)
        package_dir_name = tarball_name.split(".tar")[0] 
        if not os.path.exists(package_dir_name):
            subprocess.run(("tar -xvf sources/" + tarball_name).split(" "))
        os.chdir(package_dir_name)


    def create_and_enter_build_dir(self):
        if not os.path.exists("build"):
            os.mkdir("build")
        os.chdir("build")


    def run(self, command):
        subprocess.run(command.split(" "), env=self.env_vars, check=True)


    def run_build_commands(self, configure_flags):
        build_commands = [ "../configure " + configure_flags, 
                           "make", 
                           "make install" ]
        for command in build_commands:
            self.run(command)


    def clean_up_build(self, package_name):
        tarball_name = self.get_tarball_name(package_name)
        package_dir_name = tarball_name.split(".tar")[0] 
        os.chdir(self.root_dir)
        shutil.rmtree(package_dir_name)


    def record_new_files(self, filename):
        new_files = self.system_snapshot() - self.all_files
        with open(filename, "w") as f:
            f.writelines([file + "\n" for file in new_files])
        self.all_files = self.all_files.union(new_files)


    def build(self,
              search_term, 
              configure_flags, 
              tracked_file_path,
              before_build=None,
              after_build=None,
              custom_build=None,
              use_build_dir=True):
        self.untar_and_enter_source_dir(search_term)
        if before_build:
            before_build()
        if use_build_dir:
            self.create_and_enter_build_dir()
        if custom_build:
            custom_build()
        else:
            self.run_build_commands(configure_flags)
        if after_build:
            after_build()
        self.clean_up_build(search_term)
        self.record_new_files(tracked_file_path)


    def build_cross_binutils(self):
        configure_flags = f"--prefix={self.root_dir}/tools " \
            f"--with-sysroot={self.root_dir} --target={self.lfs_tgt} " \
            "--disable-nls --enable-gprofng=no --disable-werror"
        self.build("binutils", configure_flags, "cross-binutils") 

    
    def cross_gcc_before_build(self):
        for dep in ["mpfr", "gmp", "mpc"]:
            tarball_name = self.get_tarball_name(dep)
            self.run(f"tar -xvf {self.root_dir}/sources/{tarball_name}")
            package_dir_name = tarball_name.split(".tar")[0]
            self.run(f"mv {package_dir_name} {dep}")

        shutil.copyfile("gcc/config/i386/t-linux64",
                        "gcc/config/i386/t-linux64.orig")
        with open("gcc/config/i386/t-linux64", "r") as f:
            lines = f.readlines()
        for line in lines:
            if "m64=" in line:
                line = line.replace("lib64", "lib")
        with open("gcc/config/i386/t-linux64", "w") as f:
            f.writelines(lines)


    def cross_gcc_after_build(self):
        os.chdir("..")
        lines = []
        for file in ["gcc/limitx.h", "gcc/glimits.h", "gcc/limity.h"]:
            with open(file, "r") as f:
                lines += f.readlines()
        completed = subprocess.run(
                f"{self.lfs_tgt}-gcc -print-libgcc-file-name".split(" "),
                capture_output=True, env=self.env_vars)
        dirname = completed.stdout.decode().rsplit("/",1)[0]
        with open (dirname + "/install-tools/include/limits.h", "w") as f:
            f.writelines(lines)


    def build_cross_gcc(self):
        configure_flags = f"--target={self.lfs_tgt} " \
            f"--prefix={self.root_dir}/tools --with-glibc-version=2.37 " \
            f"--with-sysroot={self.root_dir} --with-newlib " \
            "--without-headers --enable-default-pie --enable-default-ssp " \
            "--disable-nls --disable-shared --disable-multilib " \
            "--disable-threads --disable-libatomic --disable-libgomp " \
            "--disable-libquadmath --disable-libssp --disable-libvtv " \
            "--disable-libstdcxx --enable-languages=c,c++"
        self.build("gcc", configure_flags, "cross-gcc",
                   before_build=self.cross_gcc_before_build,
                   after_build=self.cross_gcc_after_build)


    def copy_linux_headers(self):
        source = "usr/include"
        destination = self.root_dir
        if not os.path.exists(destination):
            os.mkdir(destination)
        files = [source]
        while files:
            curr = files.pop()
            if os.path.isdir(curr):
                files += [ curr + "/" + f for f in os.listdir(curr) ]
                os.mkdir(destination + "/" + curr)
            elif curr[-2:] == ".h":
                shutil.copy(curr, destination + "/" + curr)


    def linux_headers_custom_build(self):
        self.run("make mrproper")
        self.run("make headers")


    def build_linux_headers(self):
        self.build("linux-6", "", "linux-headers",
                   after_build=self.copy_linux_headers,
                   custom_build=self.linux_headers_custom_build,
                   use_build_dir=False)


    def build_system(self):
        self.build_cross_binutils()
        self.build_cross_gcc()
        self.build_linux_headers()




        

# see if i can get away with no pre and post modifications gcc 

if __name__ == '__main__':
    Alfs().build_system()

