# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-10-26

### Fixed

- With `consumer_factory`, a thread's consumer is now flushed and released when the thread exits. Before, the client
  held every consumer it had made, and events buffered by exited threads (such as idle workers a thread pool retires)
  waited until the next `flush()`. `flush()` also releases any exited thread's consumer still held
- Leaving a `with` block that raised no longer replaces its exception with a flush error under `on_error="raise"`;
  the flush error is logged instead
- The `mixpanel` extra is limited to `mixpanel>=4.0,<6`
- `__version__` falls back to `0.0.0` instead of a stale hardcoded version when package metadata is missing

## [0.1.0] - 2026-10-26

First release, published to PyPI as `altissimo-mixpanel`. The import name is
`altissimo.mixpanel`. Licensed under Apache-2.0.

### Added

- `MixpanelClient` with typed wrappers for `track`, `people_set`, `people_set_once`, `people_increment`, `people_union`, `people_unset`, and `alias`
- `MixpanelClient.from_env()` factory. A missing token disables tracking with a warning naming the variable,
  raises `ValueError` when `enabled=True` was passed, and is silent when tracking was turned off
  ([#10](https://github.com/altissimo-hq/mixpanel-python/issues/10)). It takes a `consumer` or `consumer_factory`, like
  the constructor
- One client can be shared across threads: each thread gets its own Mixpanel SDK instance (and HTTP session).
  `consumer_factory` makes one consumer per thread; `flush()` flushes all of them
  ([#12](https://github.com/altissimo-hq/mixpanel-python/issues/12))
- Configurable error handling via `on_error` parameter (`log`, `raise`, `ignore`). A missing `mixpanel` SDK is
  logged once and disables the client, instead of logging a traceback on every call (raised with `"raise"`)
- `MixpanelConsumer` protocol describing what a custom consumer needs (`send(endpoint, json_message)`)
- `MixpanelClient.flush()` and context-manager use (`with MixpanelClient(...) as client:`) to send what a
  buffering consumer such as `BufferedConsumer` is holding, so buffered events aren't lost on shutdown
  ([#9](https://github.com/altissimo-hq/mixpanel-python/issues/9))
- `MixpanelClientProtocol` for dependency injection
- `FakeMixpanelClient` test helper (`flush_count` records `flush()` calls)
- `MixpanelError` and `MixpanelImportError` exception hierarchy
- Lazy SDK import — zero import-time side effects
- PEP 561 `py.typed` marker
- CI pipeline with lint, test (Python 3.11–3.13), and build stages, using Poetry 2.4.1 with actions pinned by
  commit
- A publish workflow: tagged releases (`v*`) are tested, checked against the package version, built, and uploaded
  to PyPI through Trusted Publishing (environment `pypi`). Running it by hand uploads the current branch to
  TestPyPI (environment `testpypi`).
- Renovate configuration, using the shared `altissimo-hq/renovate-config` preset
