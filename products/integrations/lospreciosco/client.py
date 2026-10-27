"""HTTP client and error handling for the Los Precios API.

Talks only to the API: handles authentication, the global rate limit
(1 request per second), retries with backoff, and exposes one function per
endpoint. Also defines the exceptions raised for API ErrorIDs, split into
fatal (invalid or disabled key), retryable (too many requests) and
per-item errors (missing product, item or store).

Does not import Django and knows nothing about the database or the pipeline.
"""