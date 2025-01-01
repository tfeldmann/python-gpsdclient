from pathlib import Path
from unittest import mock

import pytest

from gpsdclient import GPSDClient, cli

from ._fake_server import VERSION_HEADER

TEST_DATA = {
    "release": "1.2.fake",
    "devices": [{"path": "/dev/ttyS0"}, {"path": "/dev/ttyAMA1"}],
}


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


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (TEST_DATA, "Connected to gpsd v1.2.fake"),
        ({}, "Connected to gpsd vn/a"),
    ],
)
def test_print_version(capsys, data, expected):
    cli.print_version(data)

    captured = capsys.readouterr()

    assert captured.err == ""
    assert captured.out == expected + "\n"


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (TEST_DATA, "Devices: /dev/ttyS0, /dev/ttyAMA1"),
        ({}, "Devices: "),
    ],
)
def test_print_devices(capsys, data, expected):
    cli.print_devices(data)

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == expected + "\n"


def test_print_tpv_header(capsys):
    cli.print_tpv_header()

    captured = capsys.readouterr()

    assert captured.err == ""
    assert captured.out.startswith("\n")
    assert captured.out.endswith("\n")
    assert "Mode |" in captured.out
    assert "| Time                 |" in captured.out
    assert "| Lat          |" in captured.out
    assert "| Lon          |" in captured.out
    assert "| Track     |" in captured.out
    assert "| Speed  |" in captured.out
    assert "| Alt       |" in captured.out
    assert "| Climb" in captured.out


def test_print_tpv_row(capsys):
    cli.print_tpv_row({"mode": 0})

    captured = capsys.readouterr()

    assert captured.err == ""
    assert len(captured.out.split(" | ")) == len(cli.TPV_COLUMNS)


def test_stream_readable(mock_client, capsys):
    cli.stream_readable(mock_client)

    captured = capsys.readouterr()

    assert captured.err == ""
    assert len(captured.out) > 0
    assert len(captured.out.splitlines()) > 0
    assert not captured.out.startswith(VERSION_HEADER)


def test_stream_json(mock_client, capsys):
    cli.stream_json(mock_client)

    captured = capsys.readouterr()

    assert captured.err == ""
    assert len(captured.out) > 0
    assert len(captured.out.splitlines()) > 0
    assert captured.out.startswith(VERSION_HEADER)
