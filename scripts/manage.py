#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from typing import Literal

import setuptools

MajorVersion = Literal["12", "13", "14", "develop"]
SemVerType = Literal["major", "minor", "micro"]
IMAGE_NAME = "ghcr.io/castlecraft/frappe_containers/erpnext"
NO_UPDATE = "NO_UPDATE"
ERPNEXT = "erpnext"
CHART_FILE = "charts/erpnext/Chart.yaml"
VALUES_FILE = "charts/erpnext/values.yaml"


def get_latest_tag(version: MajorVersion) -> str:
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
            f"https://github.com/frappe/erpnext",
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


def update_compose(file_name: str, version: str):
    with open(file_name, "r+") as f:
        content = f.read()
        content = re.sub(rf"{IMAGE_NAME}:.*", f"{IMAGE_NAME}:{version}", content)
        f.seek(0)
        f.truncate()
        f.write(content)


def update_values(version: str):
    with open(VALUES_FILE, "r+") as f:
        content = f.read()
        content = re.sub(rf"tag:.*", f"tag: {version}", content)
        f.seek(0)
        f.truncate()
        f.write(content)


def update_chart(chart_version: str, app_version: str):
    with open(CHART_FILE, "r+") as f:
        content = f.read()
        content = re.sub(rf"version: .*", f"version: {chart_version}", content, count=1)
        content = re.sub(
            rf"appVersion: .*", f"appVersion: {app_version}", content, count=1
        )
        f.seek(0)
        f.truncate()
        f.write(content)


def get_chart_versions():
    chart_versions = subprocess.check_output(
        f"yq '.version, .appVersion' < {CHART_FILE}",
        shell=True,
    )
    version, app_version = chart_versions.decode("utf-8").strip().split("\n")
    return {
        "version": version,
        "app_version": app_version,
    }


def get_values_versions():
    proc = subprocess.check_output(
        f'yq ".image.tag" < {VALUES_FILE}',
        shell=True,
    )
    version = setuptools.version.pkg_resources.parse_version(proc.decode("utf-8"))
    return version


def increment_semver(version: str, incr_type: SemVerType):
    current_version = setuptools.version.pkg_resources.parse_version(version)
    if incr_type == "major":
        return f"{current_version.major + 1}.{current_version.minor}.{current_version.micro}"
    elif incr_type == "minor":
        return f"{current_version.major}.{current_version.minor + 1}.{current_version.micro}"
    elif incr_type == "micro":
        return f"{current_version.major}.{current_version.minor}.{current_version.micro + 1}"


def verify_increment(current_version, increment_version):
    return setuptools.version.pkg_resources.parse_version(
        increment_version,
    ) > setuptools.version.pkg_resources.parse_version(
        current_version,
    )


def parse_args():
    parser = argparse.ArgumentParser("manage")
    parser.add_argument(
        "--version", choices=["12", "13", "14", "develop"], required=True
    )
    subparsers = parser.add_subparsers(help="manage help", dest="command")
    subparsers.add_parser("update-compose", help="update compose yaml(s)")
    verify_git_ver_parser = subparsers.add_parser(
        "verify-git-version", help=f"verify git version or return {NO_UPDATE}"
    )
    verify_git_ver_parser.add_argument(
        "--update-version-json",
        action="store_true",
        help="update version json file in repo",
    )
    verify_git_ver_parser.add_argument(
        "--display",
        action="store_true",
        help=f"display version instead of {NO_UPDATE}",
    )
    update_helm_parser = subparsers.add_parser(
        "update-helm", help="update Chart.yaml and values.yaml"
    )
    update_helm_parser.add_argument(
        "--increment", choices=["major", "minor", "micro"], required=True
    )
    return parser


def verify_git_version(args):
    if args.version == "develop":
        return print(NO_UPDATE)
    version_file = f"versions/version-{args.version}.json"
    repo_versions = get_versions(version_file=version_file, version=args.version)
    is_valid_increment = verify_increment(
        repo_versions.get("local_version"),
        repo_versions.get("repo_version"),
    )
    if is_valid_increment:
        print(repo_versions.get("repo_version"))
        if args.update_version_json:
            versions = {}
            versions[ERPNEXT] = repo_versions.get("repo_version")
            with open(version_file, "w") as json_file:
                print(json.dumps(versions, indent=2), file=json_file)
    else:
        print(repo_versions.get("repo_version") if args.display else NO_UPDATE)


def get_versions(version_file: str, version: MajorVersion):
    versions = {}
    repo_version = get_latest_tag(version)
    with open(version_file) as f:
        versions = json.load(f)
    local_version = versions.get(ERPNEXT)
    return {
        "repo_version": repo_version,
        "local_version": local_version,
    }


def update_compose_files(args):
    if args.version == "develop":
        return print(NO_UPDATE)
    version_file = f"versions/version-{args.version}.json"
    versions = get_versions(version_file=version_file, version=args.version)
    update_compose("compose.yml", versions.get("repo_version"))


def update_helm_files(args):
    if args.version == "develop":
        return print(NO_UPDATE)
    repo_version = get_latest_tag(args.version)
    chart_versions = get_chart_versions()
    chart_increment = increment_semver(
        chart_versions.get("version"),
        incr_type=args.increment,
    )
    values_version = str(get_values_versions())
    is_chart_increment_valid = verify_increment(
        chart_versions.get("version"),
        chart_increment,
    )
    is_chart_version_valid = verify_increment(
        chart_versions.get("app_version"),
        repo_version,
    )
    is_values_increment_valid = verify_increment(
        values_version,
        repo_version,
    )
    if (
        is_chart_increment_valid
        and is_values_increment_valid
        and is_chart_version_valid
    ):
        update_chart(chart_increment, repo_version)
        update_values(repo_version)
    else:
        print(NO_UPDATE)


def main(_args: list[str]):
    args = parse_args().parse_args()
    if args.command == "update-compose":
        update_compose_files(args)
    elif args.command == "update-helm":
        update_helm_files(args)
    elif args.command == "verify-git-version":
        verify_git_version(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
