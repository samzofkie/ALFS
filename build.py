"""This module exports the build function which untars, configures, compiles and
installs a target from its source code.

Some vocab:
    * 'target' is the name a specific build of a program from it's source code.
      I'm using it to distinguish different programs that are built from the
      same source code at different phases in the whole system build, for
      example 'cross-binutils' refers to the build of the binutils utilities for
      the cross compiler toolchain, at the beginning of the whole system build,
      whereas plain 'binutils' is the target name for the build of the binutils
      utilities for the final system.
    * 'search term' is a name that can be given to _search_for_tarball that will
      produce one source code tarball. It should be able to be derived from
      'target', like 'cross-binutils' and 'binutils' should both map to
      'binutils'.
    * 'package name' refers to the search term, but with a version number.
      'binutils' should become the string 'binutils-X.Y'. Note that this is
      usually the same as the name of the directory holding all the untar-ed
      source code.
    * 'tarball name' refers to the package name with '.tar.xz' or '.tar.gz'
      appended to it, depending on the format in wget-list / the source
      directory.
"""

import os
import subprocess
import shutil
from setup import ROOT_DIR, ENV_VARS, record_new_files


def _clean_target_name(target_name):
    search_term = target_name.replace("cross-","")
    search_term = search_term.replace("temp-", "")
    return search_term


def _search_for_tarball(search_term):
    tarballs = os.listdir(f"{ROOT_DIR}/sources")
    res = [tarball for tarball in tarballs if search_term in tarball]
    res = [tarball for tarball in res if ".patch" not in tarball]
    if len(res) < 1:
        raise FileNotFoundError("No results from search term \"" +
                                   search_term + "\"")
    elif len(res) > 1:
        raise FileNotFoundError("Too many results from search term \"" +
                                search_term + "\": " + str(res))
    return res[0]


def get_tarball_and_package_names(search_term):
    tarball_name = _search_for_tarball(search_term)
    package_name = tarball_name.split(".tar")[0]
    return tarball_name, package_name


def _untar_and_enter_source_dir(tarball_name, package_name):
    os.chdir(ROOT_DIR)
    if not os.path.exists(package_name):
        subprocess.run(("tar -xvf sources/" + tarball_name).split(" "))
    os.chdir(package_name)


def create_and_enter_build_dir():
    if not os.path.exists("build"):
        os.mkdir("build")
    os.chdir("build")


def run(command, _env=ENV_VARS):
    subprocess.run(command.split(), env=_env, check=True)


def _run_build_commands(configure_command, cl_args):
    build_commands = [configure_command, "make", "make install"]
    for command in build_commands:
        _env = ENV_VARS.copy()
        if command in cl_args:
            for arg in cl_args[command]:
                _env[arg] = cl_args[command][arg]
        print(f"running {command} w env: {_env}")
        run(command, _env)


def _clean_up_build(package_name):
    os.chdir(ROOT_DIR)
    shutil.rmtree(package_name)


def build(target_name,
          search_term = "",
          before_build = None,
          build_dir = True,
          configure_command = "",
          build_cl_args = {},
          #destdir = "",
          after_build = None):
    """Compile and install a target from source code.

    """
    os.chdir(ROOT_DIR)
    if not search_term:
        search_term = _clean_target_name(target_name)
    tarball_name, package_name = get_tarball_and_package_names(search_term)
    
    _untar_and_enter_source_dir(tarball_name, package_name)
    if before_build: 
        before_build()
    if build_dir:
        create_and_enter_build_dir()
    if configure_command:
        _run_build_commands(configure_command, build_cl_args)
    if after_build:
        after_build()
    _clean_up_build(package_name)

    record_new_files(target_name)

    

