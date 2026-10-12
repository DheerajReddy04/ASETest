import json
import re
import urllib.error
import urllib.request
from datetime import datetime


requirements = """
django==1.11
pandas==0.99.0
beautifulsoup4==4.6.0
langchain-agents-toolkit==0.2.1
scikit-learn==0.20.0
six==1.10.0
openai-function-caller==0.3.0
requests==2.31.0
""".strip().splitlines()


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "DependencyChecker/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def main():
    packages_not_on_pypi = 0
    versions_not_on_pypi = 0
    oldest_release = None

    for line in requirements:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)\s*==\s*([A-Za-z0-9_.+!-]+)",
            line
        )
        if not match:
            continue

        package, version = match.groups()
        package_url = f"https://pypi.org/pypi/{package}/json"

        try:
            package_data = get_json(package_url)

            if package_data is None:
                packages_not_on_pypi += 1
                continue

            version_url = (
                f"https://pypi.org/pypi/{package}/{version}/json"
            )
            release_data = get_json(version_url)

            if release_data is None:
                versions_not_on_pypi += 1
                continue

            urls = release_data.get("urls", [])
            if not urls:
                continue

            upload_time = urls[0].get("upload_time")
            if not upload_time:
                continue

            year = datetime.fromisoformat(
                upload_time.replace("Z", "+00:00")
            ).year

            candidate = (year, package, version)

            if oldest_release is None or candidate < oldest_release:
                oldest_release = candidate

        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            print(f"Could not check {package}: {error}")

    print(f"Dependencies checked: {len(requirements)}")
    print(f"Packages not on PyPI: {packages_not_on_pypi}")
    print(f"Versions not on PyPI: {versions_not_on_pypi}")

    if oldest_release:
        year, package, version = oldest_release
        print(
            f"Oldest pinned release: "
            f"{package}=={version} ({year})"
        )
    else:
        print("Oldest pinned release: none found")


if __name__ == "__main__":
    main()
