from __future__ import annotations

import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest

from gpsdclient import GPSDClient
from gpsdclient.client import parse_datetime

from ._fake_server import VERSION_HEADER, fake_server


@pytest.fixture(params=[{"want_pps": True}, {"want_pps": False}])
def mock_client(request: pytest.FixtureRequest):
    if request.param["want_pps"]:
        gpsd_output = Path("tests/example_output_with_toff.jsonl").read_text()
    else:
        gpsd_output = Path("tests/example_output.jsonl").read_text()

    with (
        mock.patch.object(
            GPSDClient,
            "gpsd_lines",
            return_value=(VERSION_HEADER + gpsd_output).splitlines(),
        ),
        GPSDClient() as client,
    ):
        yield client


@pytest.fixture(params=[{"want_pps": True}, {"want_pps": False}])
def server_client(request: pytest.FixtureRequest):
    server = threading.Thread(target=fake_server)
    server.start()

    # wait for server thread coming alive
    time.sleep(1.0)
    while not server.is_alive():
        time.sleep(0.1)

    with GPSDClient(port=20000, want_pps=request.param["want_pps"]) as client:
        yield client


FILTER_TESTCASES: list[tuple] = [
    ([], [9, 12]),
    (["TPV", "SKY"], 6),
    ("TPV,SKY", 6),
    (["TPV"], 3),
    ("TPV", 3),
    (["SKY"], 3),
    ("SKY", 3),
]


@pytest.mark.parametrize(("filter_spec", "count"), FILTER_TESTCASES)
def test_json_stream_filter(
    mock_client: GPSDClient, filter_spec: list[str] | str, count: int | list[int]
):
    # Test that filtering the JSON stream produces the expected number of lines
    lines = list(mock_client.json_stream(filter_spec=filter_spec))
    if isinstance(count, int):
        assert len(lines) == count
    else:
        assert len(lines) in count


@pytest.mark.parametrize(("filter_spec", "count"), FILTER_TESTCASES)
def test_dict_stream_filter(
    mock_client: GPSDClient, filter_spec: tuple, count: int | list[int]
):
    # Test that filtering the dict stream produces the expected number of lines
    lines = list(mock_client.dict_stream(filter_spec=filter_spec))
    if isinstance(count, int):
        assert len(lines) == count
    else:
        assert len(lines) in count


@pytest.mark.parametrize(
    ("input", "output"),
    [
        ("2021-08-13T09:12:42.000Z", datetime(2021, 8, 13, 9, 12, 42, 0, timezone.utc)),
        (1662215327.967219, datetime(2022, 9, 3, 14, 28, 47, 967219, timezone.utc)),
        ("yesterday", "yesterday"),
        (object, object),
    ],
)
def test_parse_datetime(input, output):  # noqa: A002
    assert output == parse_datetime(input)


@pytest.mark.parametrize(
    ("convert", "timetype"),
    [
        (True, datetime),
        (False, str),
    ],
)
def test_dict_time_conversion(mock_client: GPSDClient, convert, timetype):
    for line in mock_client.dict_stream(filter_spec="TPV", convert_datetime=convert):
        if "time" in line:
            assert isinstance(line["time"], timetype)


def test_json_stream(server_client: GPSDClient):
    output = "\n".join(server_client.json_stream())
    assert (
        output.splitlines()[0] == VERSION_HEADER.strip()
    ), "Version Header was not received"
    assert len(output) > len(VERSION_HEADER), "Only the Version Header was received"
    assert ",}" not in output, "Trailing commas were not stripped"


def test_dict_stream(server_client: GPSDClient):
    count = 0
    for row in server_client.dict_stream():
        if row["class"] == "TPV":
            count += 1
    assert count == 3


def test_dict_filter(server_client: GPSDClient):
    counter = Counter()
    for row in server_client.dict_stream(filter_spec=["SKY"]):
        print(row)
        counter[row["class"]] += 1

    assert counter["TPV"] == 0
    assert counter["SKY"] == 3
    assert counter["TOFF"] == 0


def test_dict_filter_multiple(server_client: GPSDClient):
    counter = Counter()
    for row in server_client.dict_stream(filter_spec=["SKY", "TPV"]):
        counter[row["class"]] += 1
    assert counter["TPV"] == 3
    assert counter["SKY"] == 3
    assert counter["TOFF"] == 0


def test_dict_filter_pps(server_client: GPSDClient):
    counter = Counter()
    for row in server_client.dict_stream(filter_spec=["SKY", "TOFF"]):
        counter[row["class"]] += 1

    assert counter["TPV"] == 0
    assert counter["SKY"] == 3
    assert counter["TOFF"] in [0, 3]
