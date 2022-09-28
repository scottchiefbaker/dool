#!/usr/bin/python3

import sys
import glob
import os
import shutil
import pathlib

base_dir = os.path.dirname(__file__)
base_dir = base_dir or "."
am_root  = os.getuid() == 0

# Options for --user and --root install
argv = sys.argv[1:]
args = " ".join(argv)

force_root_install = args.__contains__("--root")
force_user_install = args.__contains__("--user")

# --user overrides --root
if (force_user_install):
    force_root_install = False
    am_root            = False

# Glob the files we need to install
binaries = glob.glob(base_dir + "/dool")
plugins  = glob.glob(base_dir + "/plugins/*.py")
manpages = glob.glob(base_dir + "/docs/dool.1")

############################################################

def root_install(binaries, plugins, manpages):
    bindir      = "/usr/bin/"
    plugin_dir  = "/usr/share/dool/"
    manpage_dir = "/usr/share/man/man1/"

    ok = os.makedirs(bindir, exist_ok=True)
    ok = os.makedirs(plugin_dir, exist_ok=True)

    print("Installing binary in %s" % bindir)
    for x in binaries:
        file = os.path.basename(x)
        shutil.copyfile(x, bindir + "/" + file)
        os.chmod(bindir + "/" + file, 0o755)

    print("Installing plugins in %s" % plugin_dir)
    for x in plugins:
        file = os.path.basename(x)
        shutil.copyfile(x, plugin_dir + "/" + file)
        os.chmod(plugin_dir + "/" + file, 0o644)

    print("Installing manpages in %s" % manpage_dir)
    for x in manpages:
        file = os.path.basename(x)
        shutil.copyfile(x, manpage_dir + "/" + file)
        os.chmod(manpage_dir + "/" + file, 0o644)

def user_install(binaries, plugins, manpages):
    homedir    = os.path.expanduser("~/")
    bindir     = homedir + "/bin/"
    plugin_dir = homedir + "/.dool/"

    bindir     = bindir.replace("//", "/")
    plugin_dir = plugin_dir.replace("//", "/")

    ok = os.makedirs(bindir, exist_ok=True)
    ok = os.makedirs(plugin_dir, exist_ok=True)

    print("Installing binary in %s" % bindir)
    for x in binaries:
        file = os.path.basename(x)
        shutil.copyfile(x, bindir + "/" + file)
        os.chmod(bindir + "/" + file, 0o755)

    print("Installing plugins in %s" % plugin_dir)
    for x in plugins:
        file = os.path.basename(x)
        shutil.copyfile(x, plugin_dir + "/" + file)
        os.chmod(plugin_dir + "/" + file, 0o644)

############################################################

if (force_root_install or am_root):
    print("You are root, doing a system wide install\n")

    root_install(binaries, plugins, manpages)
else:
    print("You are a regular user, doing a local install\n")

    user_install(binaries, plugins, manpages)
