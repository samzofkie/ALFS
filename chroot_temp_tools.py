import os, shutil
from phase import Phase

class ChrootTempToolsBuild(Phase):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)
        self.env = {"PATH": "/usr/bin:/usr/sbin"}

        self.targets["temp_gettext"] = {
            "build_commands": ["./configure --disable-shared", "make"]
        }

    def _temp_gettext_after(self):
        for prog in ["msgfmt", "msgmerge", "xgettext"]:
            shutil.copy(f"gettext-tools/src/{prog}", "/usr/bin")
        
