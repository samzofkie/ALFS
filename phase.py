import os, subprocess, shutil, time
from collections import OrderedDict
import utils


class Phase:
    # targets = OrderedDict()
    def __init__(self, root, file_tracker):
        self.root_dir = root
        self.file_tracker = file_tracker
        self.env = os.environ.copy()
        self.targets = OrderedDict()

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

    def _clean_up_build(self, package_name):
        os.chdir(self.root_dir)
        shutil.rmtree(package_name)

    def _build_package(
        self, target_name, build_commands, search_term="", build_dir=False
    ):
        if self.file_tracker.query_record_existence(target_name):
            return
        if not search_term:
            search_term = self._clean_target_name(target_name)
        tarball_name = self._search_for_tarball(search_term)
        package_name = self._package_name_from_tarball(tarball_name)

        self._untar_and_enter_source_dir(tarball_name)
        start_time = time.time()

        self._before_build(target_name)
        if build_dir:
            self._create_and_enter_build_dir()
        for command in build_commands:
            self._run(command)
        self._after_build(target_name)

        self._clean_up_build(package_name)
        self.file_tracker.record_new_files_since(start_time, target_name)

    def build_phase(self):
        for target, args in self.targets.items():
            self._build_package(target, **args)


class PreChrootPhase(Phase):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)
        self.lfs_triplet = "x86_64-lfs-linux-gnu"
        self.host_triplet = "x86_64-pc-linux-gnu"
        self.env = {
            "LC_ALL": "POSIX",
            "PATH": f"{self.root_dir}/tools/bin:/usr/bin",
            "CONFIG_SITE": f"{self.root_dir}/usr/share/config.site",
        }

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

        shutil.copyfile("gcc/config/i386/t-linux64", "gcc/config/i386/t-linux64.orig")
        lines = utils.read_file("gcc/config/i386/t-linux64")
        for line in lines:
            if "m64=" in line:
                line = line.replace("lib64", "lib")
        utils.write_file("gcc/config/i386/t-linux64", lines)
