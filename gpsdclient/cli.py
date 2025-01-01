"""
Connect to a running gpsd instance and show human readable output.
"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections import namedtuple

from . import GPSDClient

Column = namedtuple("Column", "key width formatter")

TPV_COLUMNS = (
    Column("mode", width=4, formatter=lambda x: format(x, "^4d")),
    Column(
        "time",
        width=20,
        formatter=lambda x: x.strftime("%Y-%m-%d %H:%M:%S"),
    ),
    Column("lat", width=12, formatter=lambda x: format(x, "< 12.7n")),
    Column("lon", width=12, formatter=lambda x: format(x, "< 12.7n")),
    Column("speed", width=6, formatter=lambda x: format(x, "< 6.3n")),
    Column("track", width=9, formatter=lambda x: format(x, "< 9.5n")),
    Column("alt", width=9, formatter=lambda x: format(x, "< 9.5n")),
    Column("climb", width=9, formatter=lambda x: format(x, "< 9.5n")),
)
NA = "n/a"


def print_version(data):
    print("Connected to gpsd v{}".format(data.get("release", NA)))


def print_devices(data):
    output = ", ".join(x.get("path", NA) for x in data.get("devices", []))
    print(f"Devices: {output}")


def print_tpv_header():
    titles = (col.key.title().ljust(col.width) for col in TPV_COLUMNS)
    lines = ("-" * col.width for col in TPV_COLUMNS)
    print()
    print(" | ".join(titles))
    print("-+-".join(lines))


def print_tpv_row(data):
    values = []
    for key, width, formatter in TPV_COLUMNS:
        value = formatter(data[key]) if key in data else NA
        values.append(value.ljust(width))
    print(" | ".join(values))


def stream_readable(client):
    needs_tpv_header = True
    for x in client.dict_stream(convert_datetime=True):
        if x["class"] == "VERSION":
            print_version(x)
            needs_tpv_header = True
        elif x["class"] == "DEVICES":
            print_devices(x)
            needs_tpv_header = True
        elif x["class"] == "TPV":
            if needs_tpv_header:
                print_tpv_header()
                needs_tpv_header = False
            print_tpv_row(x)


def stream_json(client):
    for x in client.json_stream():
        print(x)


def main():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="The host running GPSD",
    )
    parser.add_argument(
        "--port",
        default="2947",
        help="GPSD port",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON strings",
    )
    parser.add_argument("--pps", action="store_true", help="Enable PPS output")
    parser.add_argument(
        "--timeout",
        default=5.0,
        help="Socket timeout in seconds",
    )
    args = parser.parse_args()

    try:
        client = GPSDClient(
            host=args.host,
            port=args.port,
            timeout=float(args.timeout),
            want_pps=args.pps,
        )
        if args.json:
            stream_json(client)
        else:
            stream_readable(client)
    except KeyboardInterrupt:
        print()
        return 0
    except OSError as e:
        print(e)
        return 1
    except Exception:
        return 2
