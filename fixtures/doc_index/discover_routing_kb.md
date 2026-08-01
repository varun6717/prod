# Card Brand Routing — How It Works

This knowledge-base page describes how the Merchant Routing Service routes authorization traffic to
the correct card brand handler. It is reference material for engineers; it does not describe a change
or a mandate.

## Supported card brands

The service routes transactions for Mastercard, Visa, and Discover. The *card brand* is resolved from
the PAN bin range during authorization.

## Routing

Once the brand is resolved, the router dispatches the message to the brand-specific handler
(`mc_handler`, `visa_handler`, `discover_handler`). Routing is table-driven and reloadable without a
deploy.

## Transaction flow

Authorization → brand resolution → handler dispatch → response normalization → ledger write. Each
step emits a span for tracing.

## Error handling

If a brand handler is unavailable, the router applies the configured fallback and records an
`EBRAND_UNAVAILABLE` error code; retries are bounded.
