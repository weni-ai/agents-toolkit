# VTEX

The VTEX module lets tools call private VTEX APIs during execution without hand-rolling HTTP. All traffic goes through Retail's generic VTEX proxy — you never talk to VTEX IO directly, and you never assemble Retail authentication yourself.

## Quick Start

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class GetOrdersTool(Tool):
    def execute(self, context: Context):
        orders = self.gallery_vtex(
            endpoint="api/oms/pvt/orders",
            method="GET",
            params={"f_status": "ready-for-handling"},
        )
        return TextResponse(data=orders)
```

`self.vtex` is a `Vtex` instance pre-bound to the tool. It is created on first access and cached for the duration of the execution.

## Calling Styles

All three styles are equivalent. Choose whichever fits your convention:

```python
# Namespaced (recommended)
orders = self.vtex.request(path="/api/oms/pvt/orders", method="GET")

# Shorthand
orders = self.gallery_vtex(endpoint="api/oms/pvt/orders", method="GET")

# Order helpers — id or query only
order = self.get_order("v1234567890-01")
document = self.get_order_document("v1234567890-01")
matches = self.search_orders("?q=user@email.com")

# Explicit — pass the tool instance yourself
from weni.vtex import Vtex
orders = Vtex(self).request(path="/api/oms/pvt/orders", method="GET")
```

`path` and `endpoint` are aliases. When both are provided, `path` wins.

## How It Works

```
   Tool.execute()                         Retail                  VTEX IO
   ──────────────                         ──────                  ───────
   self.vtex.request(path, method)
        │
        ▼
   VtexSender
   validates method + path
        │
        ▼
   RetailClient
   POST /vtex/proxy/  ─────────────────►  resolves account,
        json={ method, path, … }          signs IO JWT, forwards
                                                   │
                                                   ▼
                                          /_v/proxy-vtex  ──►  VTEX API
```

1. `request()` (and `gallery_vtex`) require a VTEX path and an HTTP method.
2. The sender rejects unsupported methods and absolute URLs before any network call.
3. Retail authenticates the project, resolves the VTEX account (and optional merchant), and forwards the call to VTEX IO.
4. The parsed JSON object or array is returned to the tool.

You do **not** pass account domain, VTEX account, or a VTEX IO token. Those stay on the Retail side.

## Request Arguments

| Argument | Required | Description |
|---|---|---|
| `path` / `endpoint` | Yes | VTEX API path. A leading slash is added if missing. Absolute `http(s)://` URLs are rejected. |
| `method` | No | `GET` (default), `POST`, `PUT`, or `PATCH`. Case-insensitive. `DELETE` is not supported. |
| `headers` | No | Extra headers forwarded to VTEX. Not used for Retail authentication. |
| `data` | No | JSON body for POST/PUT/PATCH. An empty dict or list is still sent. |
| `params` | No | Query parameters appended to the VTEX URL. |
| `merchant_name` | No | Seller account override; Retail allows it only when the project account lists that merchant as a VTEX seller. |

```python
self.vtex.request(
    path="/api/oms/pvt/orders",
    method="POST",
    headers={"Accept": "application/json"},
    data={"customer": "user@example.com"},
    params={"an": "store"},
    merchant_name="selleraccount",
)
```

The return value is the parsed JSON from VTEX — an object or an array (OMS list endpoints commonly return arrays).

## Order helpers

Frequent order calls do not need a path. These methods build it (or the dedicated Retail body) for you:

| Method | What it calls | You pass |
|---|---|---|
| `self.get_order(order_id)` | `GET /api/oms/pvt/orders/{order_id}` via `POST /vtex/proxy/` | the order id |
| `self.get_order_document(order_id)` | `GET /api/orders/pvt/document/{order_id}` via `POST /vtex/proxy/` | the order id |
| `self.search_orders(raw_query)` | `POST /vtex/orders/` with `{"raw_query": "..."}` | the query string |

```python
order = self.vtex.get_order("v1234567890-01")
document = self.vtex.get_order_document("v1234567890-01", merchant_name="selleraccount")
matches = self.vtex.search_orders("q=user@email.com")
```

`get_order` and `get_order_document` accept an optional `merchant_name`, forwarded the same way as `request()`. They do not take `headers`, `data`, or `params` — use `request()` when a call needs those.

`order_id` is stripped, then rejected when it is empty or contains `/`, `\`, `?`, `#`, or whitespace. A valid id is quoted before it is placed in the path.

`search_orders` does not go through `/vtex/proxy/`. It posts to Retail's orders endpoint, which forwards `raw_query` to VTEX IO `/get-orders`. An empty query raises `VtexValidationError`. A query without a leading `?` is prefixed (`q=user@email.com` becomes `?q=user@email.com`). The string is not re-encoded.

## Operation Log

Each successful call is recorded in the tool's operation log:

```python
{
    "result": <data>,
    "vtex_requests": [
        {"path": "/api/oms/pvt/orders", "method": "GET"},
    ]
}
```

The key only appears when at least one request succeeded. Entries include **path and method only** — headers, body, and `search_orders` query strings are omitted so VTEX app keys, tokens, and emails never land in the result payload. A search is logged as `{"path": "/vtex/orders/", "method": "POST"}`.

Entries are recorded **after** Retail succeeds. A validation error or a failed proxy call raises and leaves the log untouched.

## Configuration

Configuration is resolved by `RetailClient` when `VtexSender` is constructed:

| Value | Context keys (priority order) | Environment fallback | Required |
|---|---|---|---|
| Base URL | `retail_url` in `project` → `credentials` → `globals` | `RETAIL_BASE_URL` | No (defaults to production `https://retailsetup.weni.ai`) |
| Auth token | `auth_token` in `project` | — | Yes |

Missing token raises `VtexConfigError` at construction. The auth token is the same project JWT already used by other toolkit integrations (`context.project.auth_token`).

## Error Handling

All VTEX failures subclass `VtexError`:

```python
from weni.vtex import (
    VtexError,
    VtexConfigError,
    VtexValidationError,
    VtexHTTPError,
    VtexNetworkError,
    VtexResponseError,
)

try:
    self.vtex.request(path="/api/oms/pvt/orders")
except VtexValidationError:
    ...
except VtexHTTPError as e:
    ...  # e.status_code, e.response_body
except VtexError:
    ...
```

| Error | Raised when |
|---|---|
| `VtexConfigError` | Missing `auth_token` |
| `VtexValidationError` | Missing path, empty path, absolute URL, method other than GET/POST/PUT/PATCH, invalid `order_id`, or empty `raw_query` |
| `VtexHTTPError` | Retail responds with a non-success status — exposes `status_code` and `response_body` |
| `VtexNetworkError` | The request fails before a response is received |
| `VtexResponseError` | Success body is empty, not JSON, or not an object/array |

Raw `requests` exceptions are not leaked.

## Lower-Level API

Use `VtexSender` directly when you have a `Context` but not a `Tool`:

```python
from weni.vtex import VtexSender

sender = VtexSender(context)
orders = sender.request(path="/api/oms/pvt/orders", method="GET")
order = sender.get_order("v1234567890-01")
document = sender.get_order_document("v1234567890-01")
matches = sender.search_orders("?q=user@email.com")
```

`VtexSender.request` does not accept the `endpoint` alias — that lives on the facade only. `search_orders` on the sender does not write the tool operation log; the facade does.

## Test Definition

For testing via `weni run`, pass config through `project`:

```yaml
tests:
    test_get_orders:
        project:
            auth_token: "your-retail-jwt"
            retail_url: "https://retail.example.com"
        parameters:
            status: "ready-for-handling"
```

## Out of scope (v1)

Payment Gateway (`/vtex/payments/gateway-proxy/`) and payment-transaction (`/vtex/payments/send-transaction/`) proxies are not exposed. Use the generic proxy only for VTEX Commerce APIs.
