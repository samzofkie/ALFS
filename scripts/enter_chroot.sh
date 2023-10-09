#!/usr/bin/env -S -i bash

mount -v --bind /dev ./dev
mount -v --bind /dev/pts ./dev/pts
mount -v -t proc proc ./proc
mount -v -t sysfs sysfs ./sys
mount -v -t tmpfs tmpfs ./run
chroot .
