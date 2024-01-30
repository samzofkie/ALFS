TODO:
1) Working X11, XFCE4, Firefox packages
2) Design installer logic
3) Redesign package manager
  1) Pure Python? Reconsider bash?
4) Pick init system
5) GUI package manager frontend with pretty dependency graph?
6) Documentation
7) Solidify opinion on `/usr/*` vs. `/bin`, `/lib` symlinks

Just remember--
> There are three system names that the build knows about: the machine you are building
on (build), the machine that you are building for (host), and the machine that GCC will
produce code for (target). When you configure GCC, you specify these with ‘--build=’,
‘--host=’, and ‘--target=’.

--[GCC Internals 6.1](https://gcc.gnu.org/onlinedocs/gccint.pdf)

Also, this [shell scripting best practices guide](https://sharats.me/posts/shell-script-best-practices/) is dope.

Started using f-strings, so this is dependent on <= Python 3.6.
