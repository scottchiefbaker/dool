#!/usr/bin/python3

###############################################################################
# Simple install script that copies files to various paths and sets
# permissions on files. Nothing fancy here, just copying files around
#
# 2022-09-28 - Scott Baker
###############################################################################

import sys
import glob
import os
import shutil
import pathlib

base_dir = os.path.dirname(__file__)
base_dir = base_dir or "."

# Are you running as root?
am_root  = os.getuid() == 0

# Pull out the ARGV so we can check for somethings
argv = sys.argv[1:]
args = " ".join(argv)

# Set some global variables
force_root_install = args.__contains__("--root")
force_user_install = args.__contains__("--user")
verbose            = args.__contains__("--verbose")

# --user overrides --root
if (force_user_install):
    force_root_install = False
    am_root            = False

# Glob the files we need to install
binaries = glob.glob(base_dir + "/dool")
plugins  = glob.glob(base_dir + "/plugins/*.py")
manpages = glob.glob(base_dir + "/docs/dool.1")
homedir  = os.path.expanduser("~/")

############################################################

def main():
    if (force_root_install or am_root):
        print("You are %s, doing a local install\n" % color(9, "root"))

        bin_dir     = "/usr/bin/"
        plugin_dir  = "/usr/share/dool/"
        manpage_dir = "/usr/share/man/man1/"

        print("Installing binaries to %s" % color(15, bin_dir))
        copy_files(binaries, bin_dir, 0o755)

        print("Installing plugins  to %s" % color(15, plugin_dir))
        copy_files(plugins , plugin_dir, 0o644)

        print("Installing manpages to %s" % color(15, manpage_dir))
        copy_files(manpages, manpage_dir, 0o644)
    else:
        print("You are a %s user, doing a local install\n" % color(227, "normal"))

        bin_dir     = (homedir + "/bin/").replace("//", "/")
        plugin_dir  = (homedir + "/.dool/").replace("//", "/")
        manpage_dir = ""

        print("Installing binaries to %s" % color(15, bin_dir))
        copy_files(binaries, bin_dir, 0o755)

        print("Installing plugins  to %s" % color(15, plugin_dir))
        copy_files(plugins , plugin_dir, 0o644)

    dool_path = (bin_dir + "/dool").replace("//", "/")

    #print(os.path.exists(dool_path))

    print("")
    print("Install complete. Dool installed to %s" % (color(84, dool_path)))

############################################################

# Print a string wrapped in an ANSI color and RESET
def color(num, mystr):
    reset = '\033[0;0m'
    ret   = "\033[38;5;" + str(num) + "m" + mystr + reset

    return ret

# Copy an array of files to a destination dir and chmod each file to mode
def copy_files(files, dest_dir, mode):
    ok = os.makedirs(dest_dir, exist_ok=True)

    count = 0
    for x in files:
        basename  = os.path.basename(x)
        dest_file = dest_dir + "/" + basename
        dest_file = dest_file.replace("//", "/")

        # Copy file
        ok = shutil.copyfile(x, dest_file)
        # Chmod the file after it's copied
        os.chmod(dest_file, mode)

        if verbose:
            print("%40s => %s" % (x, dest_file))

        if (ok):
            count += 1

    return ok

################################################################

if __name__ == "__main__":
    main()
