import os
import utils


class FileTracker:
    tracked_trees = ["boot", "etc", "usr"]

    def __init__(self, root_dir):
        self.root_dir = root_dir
        utils.ensure_dir(f"{root_dir}package-records")
        self._scan()

    def _scan(self):
        os.chdir(self.root_dir)
        all_files = set()
        for d in self.tracked_trees:
            for curr_dir, _, files in os.walk(d):
                for file in files:
                    full_path = f"{self.root_dir}{curr_dir}/{file}"
                    if os.path.isfile(full_path):
                        all_files.add(full_path)
        self.tracked_files = all_files

    def record_new_files_since(self, start_time, package):
        self._scan()
        new_files = {
            file for file in self.tracked_files if start_time < os.stat(file).st_mtime
        }
        utils.write_file(
            f"{self.root_dir}package-records/{package}",
            sorted([f"{file}\n" for file in new_files]),
        )

    def record_exists(self, package):
        return os.path.exists(f"{self.root_dir}package-records/{package}")
