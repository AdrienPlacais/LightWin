#!/usr/bin/env python3
"""Prepare and create a release.

Usage:

.. code-block:: bash

   python release.py <X.Y.Z>

"""
import re
import subprocess
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import yaml


def run(
    cmd: Sequence[str], check: bool = True, text: bool = True, **kwargs
) -> subprocess.CompletedProcess:
    """Run a shell command and ensure it completes successfully.

    Parameters
    ----------
    cmd :
        The command and its arguments to run.

    Returns
    -------
    subprocess.CompletedProcess
        The result of the completed subprocess.

    """
    return subprocess.run(cmd, check=check, text=text, **kwargs)


def git_clean() -> bool:
    """Check if the Git working directory is clean.

    Returns
    -------
    bool
        True if the working directory is clean, False otherwise.

    """
    result = run(["git", "status", "--porcelain"], capture_output=True)
    return result.stdout.strip() == ""


def current_branch() -> str:
    """Give branch we are on."""
    return run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True
    ).stdout.strip()


def on_appropriate_branch(version: str) -> bool:
    """Verify that the version number is consistent with current branch.

    If the version is ``1.2.3``, we should be on the ``1.2.x`` branch.

    Parameters
    ----------
    version :
        The version string to check, in the form ``X.Y.Z``.

    Returns
    -------
    bool
        True if the current Git branch matches ``X.Y.x``, False otherwise.

    """
    try:
        branch = current_branch()
    except subprocess.CalledProcessError:
        print("Failed to get current Git branch.")
        return False

    major, minor, _ = version.split(".")
    expected_branch = f"{major}.{minor}.x"

    if branch != expected_branch:
        print(
            f"You are on branch '{branch}', but version {version} "
            f"suggests you should be on '{expected_branch}'."
        )
        return False

    print(f"Branch '{branch}' matches version {version}.")
    return True


def has_staged_changes() -> bool:
    """Tell if there are changes to commit to avoid errors."""
    result = run(["git", "diff", "--cached", "--quiet"], check=False)
    return result.returncode != 0


def update_files(version: str) -> None:
    """Update :file:`CITATION.cff` and :file:`CHANGELOG.md`.

    Parameters
    ----------
    version :
        The version string to set in the files.

    """
    today = date.today().isoformat()
    _update_citation(version, today)
    _update_changelog(version, today)


def _update_citation(version: str, today: str) -> None:
    """Update the :file:`CITATION.cff` with the given version and current date.

    Parameters
    ----------
    version :
        The version string to set in the CITATION.cff file.
    today :
        Today's date.

    """
    path = Path("CITATION.cff")
    if not path.exists():
        print("CITATION.cff not found.")
        sys.exit(1)
    with path.open() as f:
        data = yaml.safe_load(f)

    data["version"] = version
    data["date-released"] = today

    with path.open("w") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    run(["git", "add", str(path)])


def _extract_changelog_section(
    version: str, content: str
) -> tuple[str, int, re.Match[str]] | None:
    """Find the changelog section for a version.

    Parameters
    ----------
    version :
        The version string (e.g., ``"1.8.0"``).
    content :
        The full text content of :file:`CHANGELOG.md`.

    Returns
    -------
    tuple[str, int, re.Match[str]] | None
        A tuple of (matched section string, line index, match object) or None
        if not found.

    """
    pattern = rf"^## \[{re.escape(
        version
    )}\](?: -- (unreleased|\d{{4}}-\d{{2}}-\d{{2}}))?$"
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if match := re.match(pattern, line, re.IGNORECASE):
            section_lines = [line]
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    break
                section_lines.append(lines[j])
            return ("\n".join(section_lines), i, match)
    return None


def changelog_is_ok(version: str) -> bool:
    """Print the section of the changelog corresponding to the given version.

    Parameters
    ----------
    version :
        The version string whose section should be printed.

    Returns
    -------
    bool :
        If the following processes can continue.

    """
    path = Path("CHANGELOG.md")
    if not path.exists():
        print("CHANGELOG.md not found.")
        return False

    content = path.read_text()
    result = _extract_changelog_section(version, content)
    if not result:
        print(
            f"CHANGELOG.md does not contain '## [{version}]'. You may have "
            "forgotten to update it."
        )
        return False

    section, _, _ = result
    print(f"\nThe CHANGELOG section corresponding to {version} reads:")
    print(
        "   (note that the current date will be automatically appended to the "
        "version\n   number line if it is not present)"
    )
    print("=" * 79)
    print(section)
    print("=" * 79 + "\n")
    return True


def _update_changelog(version: str, today: str) -> None:
    """Add current date to version section name in :file:`CHANGELOG.md`.

    Date is appended to the line containing ``## [X.Y.Z]``. If the date is
    already present, check that it matches ``today``.

    Parameters
    ----------
    version :
        The version string to set in the :file:`CHANGELOG.md` file.
    today :
        Today's date.

    """
    path = Path("CHANGELOG.md")
    if not path.exists():
        print("CHANGELOG.md not found.")
        sys.exit(1)

    content = path.read_text()
    result = _extract_changelog_section(version, content)
    if not result:
        print(f"No section '## [{version}]' found in CHANGELOG.md.")
        sys.exit(1)

    _, index, match = result
    matched_date_or_flag = match.group(1)
    if matched_date_or_flag is None:
        print(f"No date yet, appending today's date to version {version}.")
    elif matched_date_or_flag.lower() == "unreleased":
        print(f"'unreleased' found, replacing it with today's date.")
    elif matched_date_or_flag != today:
        print(
            f"Version {version} already has date {matched_date_or_flag}, but "
            f"today is {today}. I will write today's date in CHANGELOG."
        )
        ask_user_to_continue()
    else:
        print(
            "CHANGELOG.md already contains correct date for version "
            f"{version}."
        )
        return

    lines = content.splitlines()
    lines[index] = f"## [{version}] -- {today}"

    path.write_text("\n".join(lines) + "\n")
    run(["git", "add", str(path)])


def ask_user_to_continue(
    question: str = "Is it ok for you? (y/n) ",
    error_msg: str = "Operation aborted by user.",
    count: int = 0,
) -> None:
    """Ask the user if he/she wants to continue execution of the script."""
    if count >= 3:
        print("Too many unsuccessful attempts.")
        sys.exit(1)
    answer = input(question)
    if answer.lower() == "y":
        return
    if answer.lower() == "n":
        print(error_msg)
        sys.exit(1)

    print(f"{answer = } was not understood. Please try again.")
    return ask_user_to_continue(count=count + 1)


def main() -> None:
    """Run the release process.

    This includes:
    #. Checking the Git status
    #. Checking the corresponding section in :file:`CHANGELOG.md`
    #. Updating :file:`CITATION.cff` and :file:`CHANGELOG.md`
    #. Committing changes, tagging the release, pushing to origin
    #. Switching to main, merging, pushing

    """
    if len(sys.argv) != 2:
        print("Usage: python release.py X.Y.Z")
        sys.exit(1)

    version = sys.argv[1]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print("Version must be in format X.Y.Z (e.g. 1.8.0)")
        sys.exit(1)

    tag = f"v{version}"

    if not git_clean():
        print(
            "Git working directory is not clean. Maybe there are uncommited "
            "changes."
        )
        ask_user_to_continue()

    if not on_appropriate_branch(version):
        ask_user_to_continue()

    if not changelog_is_ok(version):
        print("Operation aborted due to a CHANGELOG.md error.")
        sys.exit(1)
    ask_user_to_continue()
    update_files(version)

    if has_staged_changes():
        run(["git", "commit", "-m", f"Prepare release {tag}"])
    else:
        print("Nothing to commit.")

    run(["git", "tag", tag])
    run(["git", "push", "--set-upstream", "origin", current_branch()])
    run(["git", "push", "origin", tag])

    print(f"Release {tag} tagged and pushed!")

    print("I will merge release branch into main and push.")
    ask_user_to_continue()
    run(["git", "checkout", "main"])
    run(["git", "merge", "--no-ff", tag])
    run(["git", "push", "origin", "main"])


if __name__ == "__main__":
    main()
