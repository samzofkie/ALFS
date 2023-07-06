#!/usr/bin/env python3

import os
from urllib.request import urlopen
import subprocess
import shutil


class Alfs:
    def __init__(self):
        self.root_dir = os.getcwd()
        self.lfs_tgt = "x86_64-lfs-linux-gnu"
        self.env_vars = { "LC_ALL": "POSIX", 
             "PATH": f"{self.root_dir}/tools/bin:/usr/bin",
             "CONFIG_SITE": f"{self.root_dir}/usr/share/config.site" }
        self.system_dirs = ["etc", "var", "usr/bin", "usr/lib", "usr/sbin", 
                            "lib64", "tools"]
        self.ensure_wget_list()
        self.ensure_directory_skeleton()
        self.ensure_tarballs_downloaded()
        self.all_files = self.system_snapshot()
    

    def ensure_wget_list(self):
        if not os.path.exists("wget-list"):
            res = urlopen("https://www.linuxfromscratch.org/lfs/" \
                "downloads/stable/wget-list")
            with open("wget-list", "w") as f:
                f.writelines(res.read().decode())


    def ensure_directory_skeleton(self):
        for dir in self.system_dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)
        if not os.path.exists("sources"):
            os.mkdir("sources")
    

    def system_snapshot(self):
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


    def ensure_tarballs_downloaded(self):
        with open("wget-list", "r") as f:
            tarball_urls = [line.split("\n")[0] for line in f.readlines()]

        for url in tarball_urls:
            tarball_name = url.split("/")[-1]
            if not os.path.exists("sources/" + tarball_name): 
                print("downloading " + tarball_name + "...")
                res = urlopen(url)
                with open("sources/" + tarball_name, "wb") as f:
                    f.write(res.read())


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


    def build_cross_binutils(self):
        self.untar_and_enter_source_dir("binutils")
        self.create_and_enter_build_dir()
        self.run_build_commands(f"--prefix={self.root_dir}/tools " \
            f"--with-sysroot={self.root_dir} --target={self.lfs_tgt} " \
            "--disable-nls --enable-gprofng=no --disable-werror")
        self.clean_up_build("binutils")
        self.record_new_files("cross-binutils")


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
        lines = []
        for file in ["gcc/limitx.h", "gcc/glimits.h", "gcc/limity.h"]:
            with open(file, "r") as f:
                lines += f.readlines()
        completed = subprocess.run(
            f"dirname {self.lfs_tgt}-gcc -print-libgcc-file-name".split(" "))


    def build_cross_gcc(self):
        self.untar_and_enter_source_dir("gcc")
        self.cross_gcc_before_build()
        self.create_and_enter_build_dir()
        self.run_build_commands(f"--target={self.lfs_tgt} " \
            f"--prefix={self.root_dir}/tools --with-glibc-version=2.37 " \
            "--with-sysroot={self.root_dir} --with-newlib " \
            "--without-headers --enable-default-pie --enable-default-ssp " \
            "--disable-nls --disable-shared --disable-multilib " \
            "--disable-threads --disable-libatomic --disable-libgomp" \
            "--disable-libquadmath --disable-libssp --disable-libvtv " \
            "--disable-libstdcxx --enable-languages=c,c++")
        self.cross_gcc_after_build()
        self.clean_up_build("gcc")
        self.record_new_files("cross-gcc")

    def build_linux_headers(self):
        self.untar_and_enter_source_dir("linux-6")
        self.run("make mrproper")
        self.run("make headers")
        

a = Alfs()
a.build_cross_binutils()
a.build_cross_gcc()
