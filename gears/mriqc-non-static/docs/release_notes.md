<!-- markdownlint-disable no-emphasis-as-heading-->
# Release Notes

## 0.8.0

__Fixes__:

* Fixed parsing error that caused the gear to fail for BIDS filenames that included a session name.

__Enhancements__:

* HTML report now saved as a Flywheel-viewable zip archive.
* Removed `save_outputs` config option. All output images are now automatically included with the html report in a zip archive.
* Added `debug` config option to set log level to DEBUG.
* Metrics now stored under the `derived.IQM` custom information field.
* Added unit test coverage.

__Maintenance__:
* Updated MRIQC version to 23.1.0. from 0.15.1 (note that version naming scheme has changed).
* Updated filename parsing to match current BIDS standard (v1.9.0).

