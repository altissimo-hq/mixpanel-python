# altissimo-mixpanel

Reusable, typed Mixpanel analytics client for Altissimo projects.

## Features

- **Typed API** — full type annotations for all operations
- **Lazy SDK import** — `mixpanel` is imported only when needed, zero import-time side effects
- **Disabled mode** — silently no-op all calls when analytics isn't configured
- **Error handling** — swallow-and-log by default, configurable via `on_error`
- **Protocol for DI** — `MixpanelClientProtocol` for dependency injection
- **Test helpers** — `FakeMixpanelClient` records all calls in-memory
- **Optional dependency** — works without `mixpanel` installed (fails gracefully)

## Installation

```bash
# With the Mixpanel SDK (recommended)
pip install altissimo-mixpanel[mixpanel]

# Without the SDK (for type checking / protocol-only usage)
pip install altissimo-mixpanel
```

## Quick Start

### Using `from_env()`

```python
from altissimo.mixpanel import MixpanelClient

# Reads MIXPANEL_TOKEN from environment
# Missing token → disabled mode, with a warning (see Disabled Mode)
client = MixpanelClient.from_env()

# Track an event
client.track("user-123", "Page Viewed", properties={"page": "/home"})

# Set user profile properties
client.people_set("user-123", {"$name": "Jane Doe", "$email": "jane@example.com"})
```

### Direct Construction

```python
client = MixpanelClient(
    token="your-project-token",
    enabled=True,
    on_error="log",  # "log" | "raise" | "ignore"
)
```

### Disabled Mode

```python
# Explicitly disabled
client = MixpanelClient(token="...", enabled=False)
client.track("user-123", "Page Viewed")  # silently does nothing

# Via environment variable
# MIXPANEL_ENABLED=false → disabled
client = MixpanelClient.from_env()

# Missing token → automatically disabled, and a warning names the variable
# (no MIXPANEL_TOKEN set)
client = MixpanelClient.from_env()
assert not client.enabled
```

When the token is missing, `from_env()` behaves according to how tracking was
turned on:

| `enabled` | Missing or empty token |
| --- | --- |
| `True` (passed explicitly) | Raises `ValueError` naming the variable |
| `None` (default; `MIXPANEL_ENABLED` unset or truthy) | Disabled, one warning naming the variable |
| `False`, or `MIXPANEL_ENABLED` falsey | Disabled, no warning |

Pass `enabled=True` where a deployment must send events, so a missing secret
fails at startup instead of looking like Mixpanel going quiet. An app that only
sends events when deployed can pass that condition, e.g.
`MixpanelClient.from_env(enabled=IS_DEPLOYED)`: quiet locally, an error on a
deployment missing its token.

### Error Handling

```python
# Default: catch and log errors (analytics never crashes your app)
client = MixpanelClient(token="...", on_error="log")

# Raise errors (useful for debugging)
client = MixpanelClient(token="...", on_error="raise")

# Silently ignore errors
client = MixpanelClient(token="...", on_error="ignore")
```

### Custom Consumer

```python
from mixpanel import BufferedConsumer

# Use a buffered consumer for high-throughput
client = MixpanelClient(token="...", consumer=BufferedConsumer())
```

A `BufferedConsumer` only sends when its buffer fills, so flush it before the
process exits (a Cloud Run instance shutting down, a job or CLI command
finishing), or the buffered events are lost:

```python
client.flush()

# Or flush automatically when the block ends, even if it raises:
with MixpanelClient(token="...", consumer=BufferedConsumer()) as client:
    client.track("user-123", "Job Finished")
```

With the default consumer, which sends each message immediately, `flush()`
does nothing. A failing flush follows `on_error` like every other call.

### Testing with `FakeMixpanelClient`

```python
from altissimo.mixpanel import FakeMixpanelClient

def test_order_tracking():
    fake = FakeMixpanelClient()
    service = OrderService(mixpanel=fake)

    service.create_order(user_id="user-123", total=99.99)

    assert len(fake.tracked) == 1
    assert fake.tracked[0][1] == "Order Created"
    assert fake.tracked[0][2]["total"] == 99.99
```

### Protocol-Based Dependency Injection

```python
from altissimo.mixpanel import MixpanelClientProtocol

class OrderService:
    def __init__(self, mixpanel: MixpanelClientProtocol) -> None:
        self._mp = mixpanel

    def create_order(self, user_id: str, total: float) -> None:
        # ... business logic ...
        self._mp.track(user_id, "Order Created", properties={"total": total})
```

## API Reference

### `MixpanelClient`

| Method | Description |
|---|---|
| `track(distinct_id, event_name, *, properties?, meta?)` | Track an event |
| `people_set(distinct_id, properties, *, meta?)` | Set user profile properties |
| `people_set_once(distinct_id, properties, *, meta?)` | Set properties only if not set |
| `people_increment(distinct_id, properties, *, meta?)` | Increment numeric properties |
| `people_union(distinct_id, properties, *, meta?)` | Append to list properties |
| `people_unset(distinct_id, property_names, *, meta?)` | Remove properties |
| `alias(alias_id, original_id, *, meta?)` | Create an identity alias |

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MIXPANEL_TOKEN` | — | Mixpanel project token |
| `MIXPANEL_API_SECRET` | — | API secret for import endpoints |
| `MIXPANEL_ENABLED` | `true` | Set to `false`/`0`/`no` to disable |

## Development

```bash
# Install dependencies
poetry sync

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=altissimo --cov-report=term-missing

# Lint
poetry run ruff check .

# Format
poetry run ruff format .
```

## License

[GPL-3.0-or-later](LICENSE)
