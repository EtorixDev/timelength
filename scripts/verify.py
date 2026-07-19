from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

from etdpystyle import DOCSTRING_RULES, SPACING_RULES, Severity, check_paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
PYTHON_ROOTS = (SOURCE_ROOT, PROJECT_ROOT / "scripts", PROJECT_ROOT / "tests")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def iter_python_files() -> list[Path]:
    files: list[Path] = []

    for root in PYTHON_ROOTS:
        if root.exists():
            files.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)

    return sorted(files)


def check_py_compile() -> None:
    for path in iter_python_files():
        py_compile.compile(str(path), doraise=True)


def check_style() -> None:
    diagnostics = check_paths(PYTHON_ROOTS, relative_to=PROJECT_ROOT, select=SPACING_RULES)
    diagnostics.extend(check_paths([SOURCE_ROOT], relative_to=PROJECT_ROOT, select=DOCSTRING_RULES))

    for diagnostic in diagnostics:
        print(diagnostic)

    if any(diagnostic.severity is Severity.ERROR for diagnostic in diagnostics):
        raise RuntimeError("Style violations were found.")


def main() -> None:
    check_py_compile()
    check_style()
    run([sys.executable, "-m", "ruff", "format", "--check", "."])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "pyright"])
    run([sys.executable, "-m", "pytest", "--cov", "--cov-report=term-missing"])


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
