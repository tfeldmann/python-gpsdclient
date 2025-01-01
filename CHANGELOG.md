# Changelog

## v1.4.0 (2024-01-01)

- GPSDClient now supports a `want_pps` param to request PPS and
  TOFF stanzas from GPSd
- Added tests for the CLI

### Breaking Change

- Due to adding `pytest` as a dev-dependency, the minimum supported version
  is Python 3.9.

## v1.3.2 (2023-01-09)

- Remove timezone information from CLI output (it's always UTC).

## v1.3.1 (2022-10-31)

- Add `py.typed` for full mypy type hint support.

## v1.3.0 (2022-09-02)

- GPSDClient now supports a `timeout` param
- GPSDClient now can be used as a context manager
- Code cleanup, added more tests
- parsed datetimes now contain the UTC timezone info

## v1.2.1 (2022-01-11)

- Improved type hints

## v1.2.0 (2021-10-26)

- add `filter` argument to return only the given report classes
- Fixes json parsing (gpsd emits invalid json with trailing commas in some cases)

## v1.1.0 (2021-08-1)

- Add "Climb"-column to readable output
- Standalone client code cleanups
- Updated tests

## v1.0.0 (2021-08-13)

- Tabular data output in readable mode

## v0.2.0 (2021-08-13)

- Check whether we really connect to a gpsd daemon
- Improved error messages

## v0.1.0 (2021-08-13)

- Initial release
