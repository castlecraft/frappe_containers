#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from typing import Literal

import setuptools

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
    args = parser.parse_args(_args)
    repo_version = get_latest_tag(args.repo, args.version)
    versions = {}
    version_file = f"versions/version-{args.version}.json"
    with open(version_file) as f:
        versions = json.load(f)
    local_version = versions.get(args.repo)

    if setuptools.version.pkg_resources.parse_version(
        local_version
    ) == setuptools.version.pkg_resources.parse_version(repo_version):
        print("NO_UPDATE")
    else:
        update_compose(
            "compose.yml",
            "ghcr.io/castlecraft/frappe_containers/erpnext",
            repo_version,
        )
        print("compose.yml updated")
        update_compose(
            "compose/bench.compose.yml",
            "ghcr.io/castlecraft/frappe_containers/erpnext",
            repo_version,
        )
        print("compose/bench.compose.yml updated")

    return 0


def update_compose(file_name: str, image: str, version: str):
    with open(file_name, "r+") as f:
        content = f.read()
        content = re.sub(rf"{image}:.*", f"{image}:{version}", content)
        f.seek(0)
        f.truncate()
        f.write(content)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
