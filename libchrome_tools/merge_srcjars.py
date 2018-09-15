#!/usr/bin/env python2

"""Merges several .srcjar files."""

import argparse
import zipfile


def _main():
    parser = argparse.ArgumentParser(description="Merge several .srcjar files")
    parser.add_argument("--output", type=argparse.FileType("wb"),
                        help="The path of the output .srcjar")
    parser.add_argument("srcjar", metavar="SRCJAR", type=argparse.FileType("rb"),
                        nargs="+",
                        help="The path of the .srcjar files to merge")
    args = parser.parse_args()

    with zipfile.ZipFile(args.output, "w") as output:
        for srcjar_path in args.srcjar:
            with zipfile.ZipFile(srcjar_path, "r") as srcjar:
                for path in srcjar.namelist():
                    output.writestr(path, srcjar.read(path))


if __name__ == "__main__":
    _main()
