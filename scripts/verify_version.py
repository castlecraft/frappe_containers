#!/usr/bin/env python3

import json
import sys
import argparse
import subprocess
import re
import setuptools

from typing import Literal

Repo = Literal["frappe", "erpnext"]
MajorVersion = Literal["12", "13", "14", "develop"]


def get_latest_tag(repo: Repo, version: MajorVersion) -> str:
    if version == "develop":
        return "develop"
    regex = rf"v{version}.*"
    refs = subprocess.check_output(
        (
            "git",
            "-c",
            "versionsort.suffix=-",
            "ls-remote",
            "--refs",
            "--tags",
            "--sort=v:refname",
            f"https://github.com/frappe/{repo}",
            str(regex),
        ),
        encoding="UTF-8",
    ).split()[1::2]

    if not refs:
        raise RuntimeError(f'No tags found for version "{regex}"')
    ref = refs[-1]
    matches: list[str] = re.findall(regex, ref)
    if not matches:
        raise RuntimeError(f'Can\'t parse tag from ref "{ref}"')
    return matches[0]


def main(_args: list[str]):
    local_version = ""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", choices=["frappe", "erpnext"], required=True)
    parser.add_argument(
        "--version", choices=["12", "13", "14", "develop"], required=True
    )
    parser.add_argument("--display", action='store_true')
    args = parser.parse_args(_args)
    repo_version = get_latest_tag(args.repo, args.version)
    versions = {}
    version_file = f'versions/version-{args.version}.json'
    with open(version_file, 'r') as f:
      versions = json.load(f)
    local_version = versions.get(args.repo)
    if setuptools.version.pkg_resources.parse_version(local_version) == setuptools.version.pkg_resources.parse_version(repo_version):
      print(local_version if args.display else "NO_UPDATE")
    else:
      versions[args.repo] = repo_version
      with open(version_file, 'w') as json_file:
        json.dump(versions, json_file, indent=2)
      print(repo_version)

    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
