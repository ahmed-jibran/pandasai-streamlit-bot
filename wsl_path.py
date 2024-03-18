#!/usr/bin/env python

from __future__ import print_function

import os
import argparse
import json
import re
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert between Linux and Windows paths in WSL. "
            "If no converter is explicitely specified, an implicit one is "
            "deduced."))
    parser.add_argument("path", metavar="PATH")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-w", action="store_true",
        help=(
            "Print the Windows path equivalent to PATH, "
            "using backslashes"))
    group.add_argument(
        "-m", action="store_true",
        help=(
            "Print the Windows path equivalent to PATH, "
            "using forward slashes in place of backslashes"))
    group.add_argument(
        "-u", action="store_true",
        help="Print the Linux path equivalent to PATH")

    arguments = parser.parse_args()

    converters = [
        x for x in vars(arguments)
        if x in ["w", "m", "u"] and getattr(arguments, x)]
    if not converters:
        converter = guess_converter(arguments.path)
    else:
        converter = globals()["convert_{}".format(converters[0])]

    print(converter(arguments.path))

def is_wsl():
    return os.getenv("WSL_DISTRO_NAME") is not None

def to_windows(linux_path):
    """ Convert a Linux path to a Windows path. """
    mounts = parse_mounts()
    windows_roots =mounts[1]
    linux_root = find_root(windows_roots, linux_path, "/")
    linux_leaf = linux_path[len(linux_root):]

    windows_root = windows_roots[linux_root]
    windows_leaf = linux_leaf.replace("/", "\\")

    return "".join([windows_root, windows_leaf])

def to_windows_mix(linux_path):
    """ Convert a Linux path to a Windows path with forward slashes. """
    windows_roots = parse_mounts()[1]
    linux_root = find_root(windows_roots, linux_path, "/")
    linux_leaf = linux_path[len(linux_root):]
    windows_root = windows_roots[linux_root]

    return "".join([windows_root, linux_leaf])

def to_wsl(windows_path):
    """ Convert an absolute Windows path to a Linux path. """

    linux_roots = parse_mounts()[0]
    windows_root = find_root(linux_roots, windows_path, "\\")
    windows_leaf = windows_path[len(windows_root):]

    if not windows_leaf.startswith("\\"):
        raise Exception("Cannot convert relative Windows path")

    linux_root = linux_roots[windows_root]
    linux_leaf = windows_leaf.replace("\\", "/")

    return "".join([linux_root, linux_leaf])

def guess_converter(path):
    """ Guess the best converter (to Windows with backslashes or to Linux) for
        a path.
    """

    if re.match(r"^[a-zA-Z]:", path):
        # Drive letter and colon: Windows path
        return to_wsl
    elif re.match(r"^\\", path):
        # UNC path: convert to Linux
        return to_wsl
    elif re.match(r"^/[^/]", path):
        # Slash followed by non-slash: Linux path
        return to_windows
    else:
        raise Exception("Could not guess converter for \"{}\"".format(path))

def parse_mounts():
    """ Return a map of Windows roots to their corresponding Linux root and a
        map of Linux roots to their corresponding Windows root.

        >>> linux_roots, windows_roots = parse_mounts()
        >>> linux_roots["C:"]
        '/mnt/c'
        >>> windows_roots["/mnt/c"]
        'C:'
    """
    # Map a Windows root to a Linux root
    linux_roots = {}
    # Map a Linux root to a Windows root
    windows_roots = {}

    data = subprocess.check_output(["findmnt", "-J", "-l", "-t", "9p"])
    data = json.loads(data)
    for filesystem in data["filesystems"]:
        linux_path, windows_path = filesystem["target"], filesystem["source"]
        linux_roots[windows_path] = linux_path
        windows_roots[linux_path] = windows_path

    return linux_roots, windows_roots

def find_root(roots, path, separator):
    """ Return the root matching the given path followed by a separator. """

    candidates = [
        x for x in roots
        if path.startswith("{}{}".format(x, separator))]
    if not candidates:
        raise Exception("No root found for {}".format(path))
    elif len(candidates) > 1:
        raise Exception("Multiple roots found for {}".format(path))

    return candidates[0]

if __name__ == "__main__":
    sys.exit(main())
