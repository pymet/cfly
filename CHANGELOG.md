# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.3] - 2018-04-13

### Added

- add `output_dir` parameter to `build_module`

### Removed

- unimplement `build_executable`
- remove `execute` parameter to `build_module`

## [1.0.2] - 2018-04-08

### Added

- support peargs and postargs
- implement `build_executable` for launchers
- add `execute` parameter to `build_module`

## [1.0.1] - 2018-04-07

### Fixed

- missing `tp_as_async`, `tp_as_buffer`, `tp_as_mapping`, `tp_as_number` and `tp_as_sequence`

## [1.0.0] - 2018-04-01

[Unreleased]: https://github.com/pymet/cfly/compare/1.0.3...HEAD
[1.0.3]: https://github.com/pymet/cfly/compare/1.0.2...1.0.3
[1.0.2]: https://github.com/pymet/cfly/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/pymet/cfly/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/pymet/cfly/tree/1.0.0
