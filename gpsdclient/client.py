"""
A simple and lightweight GPSD client.
"""

from __future__ import annotations

import json
import re
import socket
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Union

# old versions of gpsd with NTRIP sources emit invalid json which contains trailing
# commas. As the json strings emitted by gpsd are well known to not contain structures
# like `{"foo": ",}"}` it should be safe to remove all commas directly before curly
# braces. (https://github.com/tfeldmann/gpsdclient/issues/1)
REGEX_TRAILING_COMMAS = re.compile(r"\s*,\s*}")

FilterType = Union[str, Iterable[str]]


def parse_datetime(x: Any) -> Any | datetime:
    """
    tries to convert the input into a `datetime` object if possible.
    """
    try:
        if isinstance(x, float):
            return datetime.fromtimestamp(x, tz=timezone.utc).replace(
                tzinfo=timezone.utc
            )
        if isinstance(x, str):
            # time zone information can be omitted because gps always sends UTC.
            result = datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%f%z")
            return result.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    return x


def create_filter_regex(reports: str | Iterable[str] = set()) -> str:
    """
    Dynamically assemble a regular expression to match the given report classes.
    This way we don't need to parse the json to filter by report.
    """
    if isinstance(reports, str):
        reports = reports.split(",")
    if reports:
        classes = {x.strip().upper() for x in reports}
        return r'"class":\s?"({})"'.format("|".join(classes))
    return r".*"


class GPSDClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: str | int = "2947",
        timeout: float | int | None = None,
        want_pps: bool = False,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.want_pps = want_pps
        self.sock = None  # type: Any

    def gpsd_lines(self):
        self.close()
        self.sock = socket.create_connection(
            address=(self.host, int(self.port)),
            timeout=self.timeout,
        )
        options = {"enable": True, "json": True}
        if self.want_pps:
            options["pps"] = True
        self.sock.send(b"?WATCH=")
        self.sock.send(
            json.dumps(options, indent=None, separators=(",", ":")).encode("utf-8")
        )
        self.sock.send(b"\n")
        yield from self.sock.makefile("r", encoding="utf-8")

    def json_stream(self, filter_spec: FilterType | None = None) -> Iterable[str]:
        if filter_spec is None:
            filter_spec = set()
        filter_regex = re.compile(create_filter_regex(filter_spec))

        expect_version_header = True
        for line in self.gpsd_lines():
            answer = line.strip()
            if answer:
                if expect_version_header and not answer.startswith(
                    '{"class":"VERSION"'
                ):
                    raise OSError(
                        "No valid gpsd version header received. Instead received:\n"
                        f"{answer[:100]}...\n"
                        "Are you sure you are connecting to gpsd?"
                    )
                expect_version_header = False

                if not filter_spec or filter_regex.search(answer):
                    cleaned_json = REGEX_TRAILING_COMMAS.sub("}", answer)
                    yield cleaned_json

    def dict_stream(
        self, *, convert_datetime: bool = True, filter_spec: FilterType | None = None
    ) -> Iterable[dict[str, Any]]:
        if filter_spec is None:
            filter_spec = set()
        for line in self.json_stream(filter_spec=filter_spec):
            result = json.loads(line)
            if convert_datetime and "time" in result:
                result["time"] = parse_datetime(result["time"])
            yield result

    def close(self):
        if self.sock:
            self.sock.close()
        self.sock = None

    def __str__(self):
        return f"<GPSDClient(host={self.host}, port={self.port})>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def __del__(self):
        self.close()
