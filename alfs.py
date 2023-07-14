#!/usr/bin/env python3

from cross_toolchain import build_cross_toolchain
from temp_tools import build_temp_tools
from chroot import mount_and_enter_chroot


if __name__ == '__main__':
    build_cross_toolchain()
    build_temp_tools()
    mount_and_enter_chroot()

# TODO
# * tracked file checking / remove package function
 


        


