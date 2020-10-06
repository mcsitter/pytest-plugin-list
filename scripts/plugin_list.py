import pathlib
import re

import requests
import tabulate

FILE_HEAD = R"""Plugins List
============

The plugins are listed automatically from PyPI.
Only PyPI projects that match "pytest-\*" are considered plugins.
Packages classified as inactive are also excluded.

"""
DEVELOPMENT_STATUS_CLASSIFIERS = (
    "Development Status :: 1 - Planning",
    "Development Status :: 2 - Pre-Alpha",
    "Development Status :: 3 - Alpha",
    "Development Status :: 4 - Beta",
    "Development Status :: 5 - Production/Stable",
    "Development Status :: 6 - Mature",
    "Development Status :: 7 - Inactive",
)


def iter_plugins():
    regex = r">([\d\w-]*)</a>"
    response = requests.get("https://pypi.org/simple")
    for match in re.finditer(regex, response.text):
        name = match.groups()[0]
        if not name.startswith("pytest-"):
            continue
        response = requests.get(f"https://pypi.org/pypi/{name}/json")
        if not response.ok:
            continue
        info = response.json()["info"]
        if "Development Status :: 7 - Inactive" in info["classifiers"]:
            continue
        for classifier in DEVELOPMENT_STATUS_CLASSIFIERS:
            if classifier in info["classifiers"]:
                status = classifier[22:]
                break
        else:
            status = "NA"
        yield {
            "name": f'`{info["name"]} <{info["project_url"]}>`_',
            "summary": info["summary"],
            "pyversions": f'.. image:: https://img.shields.io/pypi/pyversions/{info["name"]}',
            "status": status,
        }


def main():
    plugin_table = tabulate.tabulate(iter_plugins(), headers="keys", tablefmt="rst")
    plugin_list = pathlib.Path("doc", "en", "plugin_list.rst")
    plugin_list.parent.mkdir(parents=True, exist_ok=True)
    with plugin_list.open("w") as f:
        f.write(FILE_HEAD)
        f.write(plugin_table)
        f.write("\n")


if __name__ == "__main__":
    main()
