from __future__ import annotations

from importlib.metadata import version
from importlib.resources import files

import timelength


def main() -> None:
    parsed = timelength.TimeLength("1 hour and 30 minutes")

    assert timelength.__version__ == version("timelength")
    assert files("timelength").joinpath("py.typed").read_bytes() == b""
    assert parsed.result.success
    assert parsed.result.seconds == 5_400


if __name__ == "__main__":
    main()
