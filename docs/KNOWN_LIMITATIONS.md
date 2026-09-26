# Known limitations

These are current product and deployment limitations, not planned features disguised as completed work.

## Campus identity

OTP verifies contact ownership. It does not prove that a user is enrolled at a university. The current application supports institutional email-domain checks and manual admin review. University SSO or student-ID verification is not implemented.

## Recommendation data

Smart Swap, Wanted matching and marketplace recommendations start from deterministic heuristics. Meaningful offline ranking evaluation requires enough real interaction data. The evaluator intentionally does not report fabricated metrics for an empty or tiny dataset.

## Media storage

Local filesystem storage is supported for development. Production deployments should use the S3-compatible adapter with durable object storage and a public media domain.

## Payments

The local payment provider is for development. Razorpay test mode should be validated end-to-end before live credentials are enabled.

## Email and SMS

SMTP and Twilio are optional integrations. The local development environment can echo OTP values instead of sending them. That mode must remain disabled in production.

## Background jobs

Redis and the worker process are required for rate limits, caching and asynchronous tasks. A production deployment needs separate worker capacity rather than running everything in the web process.
