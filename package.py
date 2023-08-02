import os, subprocess, shutil, time
import utils


class Package:
    def __init__(self, root, file_tracker):
        self.root_dir = root
        self.file_tracker = file_tracker
        self.env = {"PATH": "/usr/bin:/usr/sbin", "CC": "gcc"}
        self.target_name = self._camel_to_snake(self.__class__.__name__)
        self.search_term = self._clean_target_name(self.target_name)

    @staticmethod
    def _camel_to_snake(class_name):
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in class_name]
        ).lstrip("_")

    @staticmethod
    def _clean_target_name(target_name):
        search_term = target_name.replace("cross_", "")
        search_term = search_term.replace("temp_", "")
        return search_term

    def _search_for_tarball(self, search_term):
        tarballs = os.listdir(f"{self.root_dir}/sources")
        res = [
            tarball
            for tarball in tarballs
            if tarball[: len(search_term)] == search_term
        ]
        res = [tarball for tarball in res if ".patch" not in tarball]
        if len(res) < 1:
            raise FileNotFoundError('No results from search term "' + search_term + '"')
        elif len(res) > 1:
            raise FileNotFoundError(
                'Too many results from search term "' + search_term + '": ' + str(res)
            )
        return res[0]

    @staticmethod
    def _package_name_from_tarball(tarball_name):
        return tarball_name.split(".tar")[0]

    def _untar_and_enter_source_dir(self, tarball_name):
        os.chdir(self.root_dir)
        package_name = self._package_name_from_tarball(tarball_name)
        if not os.path.exists(package_name):
            print(f"unpacking {package_name}")
            subprocess.run(
                f"tar -xvf sources/{tarball_name}".split(" "),
                check=True,
                capture_output=True,
            )
        os.chdir(package_name)

    @staticmethod
    def _create_and_enter_build_dir():
        utils.ensure_dir("build")
        os.chdir("build")

    def _before_build(self, target_name):
        getattr(self, f"_{target_name.replace('-','_')}_before", lambda: None)()

    def _after_build(self, target_name):
        getattr(self, f"_{target_name.replace('-','_')}_after", lambda: None)()

    def _run(self, command):
        subprocess.run(command.split(), env=self.env, check=True)

    def _run_commands(self, commands):
        for command in commands:
            self._run(command)

    def _clean_up(self, package_name):
        os.chdir(self.root_dir)
        utils.ensure_removal(package_name)

    def build(self):
        if not self.file_tracker.query_record_existence(self.target_name):
            tarball_name = self._search_for_tarball(self.search_term)
            package_name = self._package_name_from_tarball(tarball_name)

            self._untar_and_enter_source_dir(tarball_name)
            start_time = time.time()

            self._inner_build()

            self._clean_up(package_name)
            self.file_tracker.record_new_files_since(start_time, self.target_name)


def gcc_change_default_64_bit_dir():
    shutil.copyfile("gcc/config/i386/t-linux64", "gcc/config/i386/t-linux64.orig")
    utils.modify(
        "gcc/config/i386/t-linux64",
        lambda line, _: line.replace("lib64", "lib") if "m64" in line else line,
    )


class PreChrootPackage(Package):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)
        self.lfs_triplet = "x86_64-lfs-linux-gnu"
        self.host_triplet = "x86_64-pc-linux-gnu"
        self.env = {
            "LC_ALL": "POSIX",
            "PATH": f"{self.root_dir}/tools/bin:/usr/bin",
            "CONFIG_SITE": f"{self.root_dir}/usr/share/config.site",
        }
        self.config_prefix_host = f"./configure --prefix=/usr --host={self.lfs_triplet}"
        self.config_prefix_host_build = (
            self.config_prefix_host + f" --build={self.host_triplet}"
        )
        self.make_destdir = ["make", f"make DESTDIR={self.root_dir} install"]

    def _common_gcc_before(self):
        for dep in ["mpfr", "gmp", "mpc"]:
            tarball_name = self._search_for_tarball(dep)
            package_name = self._package_name_from_tarball(tarball_name)
            subprocess.run(
                f"tar -xvf " f"{self.root_dir}/sources/{tarball_name}".split(),
                check=True,
                capture_output=True,
            )
            self._run(f"mv {package_name} {dep}")
        gcc_change_default_64_bit_dir()

