# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- `MixpanelClient` with typed wrappers for `track`, `people_set`, `people_set_once`, `people_increment`, `people_union`, `people_unset`, and `alias`
- `MixpanelClient.from_env()` factory with automatic disabled mode on missing token
- Configurable error handling via `on_error` parameter (`log`, `raise`, `ignore`)
- `MixpanelClientProtocol` for dependency injection
- `FakeMixpanelClient` test helper
- `MixpanelError` and `MixpanelImportError` exception hierarchy
- Lazy SDK import — zero import-time side effects
- PEP 561 `py.typed` marker
- CI pipeline with lint, test (Python 3.11–3.13), and build stages
