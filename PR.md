# Pull Request: VTEX Proxy Integration

**Branch:** `003-vtex-proxy`
**Version:** `2.9.0`

## Summary

Gallery-agent tools can now call private VTEX APIs the same way they already read contacts: one method on `Tool`, no hand-rolled HTTP.

```python
class GetOrdersTool(Tool):
    def execute(self, context: Context):
        orders = self.gallery_vtex(
            endpoint='api/oms/pvt/orders',
            method='GET',
            params={'f_status': 'ready-for-handling'},
        )
        return TextResponse(data=orders)
```

`self.vtex.request(...)` is the namespaced equivalent. `path` and `endpoint` are aliases (`path` wins if both are set).

Traffic goes **toolkit → Retail `POST /vtex/proxy/` → VTEX IO**. The toolkit does not sign VTEX IO JWTs, resolve `*.myvtex.com`, or check seller-register. Account, merchant, and IO auth stay on Retail.

Auth reuses `context.project.auth_token` (Bearer). Retail URL resolution is `project.retail_url` → `credentials` → `globals` → `RETAIL_BASE_URL` → hardcoded staging default `https://retailsetup.stg.cloud.weni.ai`. Swap that default to production after staging tests.

v1 is the generic Commerce proxy only. Payment gateway and payment-transaction proxies are out of scope.

## Public API

| Surface | Role |
|---|---|
| `self.vtex.request(...)` | Namespaced facade (mirrors `self.contact`) |
| `self.gallery_vtex(...)` | Shorthand via `_tool_methods` |
| `VtexSender` | Validates method/path, builds the proxy body |
| `RetailClient` | URL + Bearer + error translation |
| `VtexError` and subclasses | Config, validation, HTTP, network, unreadable body |

Allowed methods: `GET`, `POST`, `PUT`, `PATCH`. Absolute `http(s)://` paths are rejected. Successful calls append `{path, method}` to `vtex_requests` in the operation log — never headers or body.

## Test plan

- [ ] Call `self.gallery_vtex(endpoint='api/oms/pvt/orders', method='GET')` from a gallery tool with `project.auth_token` set
- [ ] Confirm the same call works via `self.vtex.request(path='/api/oms/pvt/orders')`
- [ ] Confirm a missing token raises `VtexConfigError` and that omitting `retail_url` hits staging
- [ ] Confirm `DELETE` and an absolute URL raise `VtexValidationError` before any HTTP
- [ ] Confirm a failed Retail response surfaces as `VtexHTTPError` with status and body
- [ ] Confirm `vtex_requests` in the tool result contains only path and method

Automated: `poetry run ruff check .`, `poetry run mypy weni`, `poetry run pytest` — `weni/vtex/` at 100% coverage, all HTTP mocked.

## Follow-ups

- Replace `DEFAULT_RETAIL_URL` with the production Retail host after staging validation
- Optionally inject `retail_url` on the Lambda `project` payload from Retail
- Payment gateway (`/vtex/payments/gateway-proxy/`) and payment transaction (`/vtex/payments/send-transaction/`) in a later feature
