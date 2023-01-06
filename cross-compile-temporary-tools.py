#!/usr/bin/python3

from build-cross-compiler import exec_commmands_with_failure 

tarball_urls = {"m4":"https://ftp.gnu.org/gnu/m4/m4-1.4.19.tar.xz",
                "ncurses":"https://invisible-mirror.net/archives/ncurses/ncurses-6.3.tar.gz",
                "bash":"https://ftp.gnu.org/gnu/bash/bash-5.1.16.tar.gz",
                "coreutils":"https://ftp.gnu.org/gnu/coreutils/coreutils-9.1.tar.xz",
                "diffutils":"https://ftp.gnu.org/gnu/diffutils/diffutils-3.8.tar.xz",
                "file":"https://astron.com/pub/file/file-5.42.tar.gz",
                "findutils":"https://ftp.gnu.org/gnu/findutils/findutils-4.9.0.tar.xz",
                "gawk":"https://ftp.gnu.org/gnu/gawk/gawk-5.1.1.tar.xz",
                "grep":"https://ftp.gnu.org/gnu/grep/grep-3.7.tar.xz",
                "gzip":"https://ftp.gnu.org/gnu/gzip/gzip-1.12.tar.xz",
                "make":"https://ftp.gnu.org/gnu/make/make-4.3.tar.gz",
                "patch":"https://ftp.gnu.org/gnu/patch/patch-2.7.6.tar.xz",
                "sed":"https://ftp.gnu.org/gnu/sed/sed-4.8.tar.xz",
                "tar":"https://ftp.gnu.org/gnu/tar/tar-1.34.tar.xz",
                "xz":"https://www.cpan.org/src/5.0/perl-5.36.0.tar.xz"}

def download_and_unpack_sources():
    os.chdir(os.environ["LFS"] + "/srcs")
    for name in tarball_urls:
        tarball_filename = os.environ["LFS"] + "/" + tarball_urls[name].split("/")[-1]
        package_name = tarball_filename.split(".tar.xz")[0].split("/")[-1]
        if (package_name in os.listdir()):
            print("already have source for " + package_name)
            continue
        print("downloading " + tarball_urls[name] + "...")
        urllib.request.urlretrieve(tarball_urls[name], tarball_filename)
        print("unpacking " + tarball_filename + "...")
        os.system("tar -xvf " + tarball_filename + " > /dev/null")
        print("removing " + tarball_filename)
        os.system("rm " + tarball_filename)

def build_temp_m4():
    exec_commmands_with_failure([("./configure --prefix=/usr "
                                  "--host={} "
                                  "--build=$(build-aux/config.guess)".config(os.environ["LFS_TGT"])),
                                 "make", "make DESTDIR={} install".format(os.environ["LFS"]) ])

def build_ncurses_
