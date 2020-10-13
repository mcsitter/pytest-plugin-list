import datetime
import pathlib
import re

import packaging.version
import requests
import tabulate

FILE_HEAD_RST = R"""Plugins List
============

The plugins are listed automatically from PyPI.
Only PyPI projects that match "pytest-\*" are considered plugins.
Packages classified as inactive are also excluded.

"""
FILE_HEAD_HTML = R"""<h1>Plugins List</h1>
<p>The plugins are listed automatically from PyPI.
Only PyPI projects that match "pytest-\*" are considered plugins.
Packages classified as inactive are also excluded.</p>
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


def iter_plugins(tablefmt="rst"):
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
        requires = "NA"
        if info["requires_dist"]:
            for requirement in info["requires_dist"]:
                if requirement == "pytest" or "pytest " in requirement:
                    requires = requirement
                    break
        releases = response.json()["releases"]
        for release in sorted(
            releases,
            key=packaging.version.parse,
            reverse=True,
        ):
            if releases[release]:
                release_date = datetime.date.fromisoformat(
                    releases[release][-1]["upload_time_iso_8601"].split("T")[0]
                )
                last_release = release_date.strftime("%b %d, %Y")
        if tablefmt == "rst":
            name = f'`{info["name"]} <{info["project_url"]}>`_'
            pyversions = (
                f'.. image:: https://img.shields.io/pypi/pyversions/{info["name"]}'
            )
        elif tablefmt == "html":
            name = f'<a href="{info["project_url"]}">{info["name"]}</a>'
            pyversions = (
                f'<img src="https://img.shields.io/pypi/pyversions/{info["name"]}">'
            )
        summary = info["summary"].replace("\n", "")
        yield {
            "name": name,
            "summary": summary,
            "pyversions": pyversions,
            "last release": last_release,
            "status": status,
            "requires": requires,
        }


def main(tablefmt="rst"):
    plugin_table = tabulate.tabulate(
        list(iter_plugins(tablefmt=tablefmt)), headers="keys", tablefmt=tablefmt
    )
    if tablefmt == "rst":
        plugin_list = pathlib.Path("doc", "en", "plugin_list.rst")
        content = FILE_HEAD_RST + plugin_table + "\n"
    elif tablefmt == "html":
        for pattern in (
            ("&lt;a", "<a"),
            ("&lt;/a&gt;", "</a>"),
            ("&lt;img", "<img"),
            ("&quot;&gt;", '">'),
            ("&quot;", '"'),
        ):
            plugin_table = plugin_table.replace(*pattern)
        plugin_list = pathlib.Path("index.html")
        from bs4 import BeautifulSoup

        content = BeautifulSoup(FILE_HEAD_HTML + plugin_table, "html.parser").prettify()

    plugin_list.parent.mkdir(parents=True, exist_ok=True)
    with plugin_list.open("w") as f:
        f.write(content)


if __name__ == "__main__":
    import sys

    tablefmt = sys.argv[1] if len(sys.argv) > 1 else "rst"
    main(tablefmt=tablefmt)
