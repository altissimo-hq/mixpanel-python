# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- `MixpanelClient` with typed wrappers for `track`, `people_set`, `people_set_once`, `people_increment`, `people_union`, `people_unset`, and `alias`
- `MixpanelClient.from_env()` factory. A missing token disables tracking with a warning naming the variable,
  raises `ValueError` when `enabled=True` was passed, and is silent when tracking was turned off
  ([#10](https://github.com/altissimo-hq/mixpanel-python/issues/10)). It takes a `consumer`, like the constructor
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
- CI pipeline with lint, test (Python 3.11–3.13), and build stages
