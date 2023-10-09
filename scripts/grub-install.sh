#!/usr/bin/env -S -i /usr/bin/bash
#
# mkfs -v -t ext4 /dev/sdxx
# mkswap /dev/sdxx
# mkfs.vfat /dev/sdxx
#
# Ok make sure that the EFI System Partition (ESP) is mounted at boot/efi, and it has it's VFAT filesystem on it, and you're chrooted before you do this

grub-install --target=x86_64-efi --removable
grub-mkconfig > /boot/grub/grub.cfig

# then add nomodeset to the linux command in the main menu entry ok
#
# also passwd
