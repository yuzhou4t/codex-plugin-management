---
name: stripe-best-practices
description: Guide specialized Stripe work outside a standard Vercel payment flow, especially Connect platforms and marketplaces, Treasury or embedded financial accounts, legacy Stripe migrations, and non-Vercel integrations that require choosing among Stripe APIs. Use when the user explicitly names these Stripe platform concerns or asks to review an existing advanced Stripe integration. For ordinary payments or subscriptions in a Vercel app, defer to the installed Vercel payments skill.
---

# Stripe Platform Routing

Use this skill for Stripe-specific platform decisions that are not already owned by the standard Vercel payments workflow.

## Verify the current Stripe contract

Stripe APIs, SDKs, product availability, and recommended integration paths change. Before giving implementation advice or writing code:

1. Inspect the project's installed Stripe SDK, existing endpoints, webhook handling, and any pinned API version.
2. Consult the current official Stripe documentation for the exact product and language.
3. Treat the bundled references as decision aids only; current official documentation overrides them.
4. Do not claim a fixed "latest" API version from this skill.
5. Do not silently upgrade an existing integration or change its pinned API version. Explain the migration impact first.

Use only Stripe's official documentation for current API behavior. Link the relevant pages in the handoff when a version-sensitive decision was made.

## Route the request

| Request | Route |
|---|---|
| Connect platform, marketplace, connected accounts, charge ownership | Read [references/connect.md](references/connect.md), then verify the current Connect docs |
| Treasury, embedded financial accounts, or money movement | Read [references/treasury.md](references/treasury.md), then verify current product availability and API docs |
| Legacy Charges, Sources, Tokens, account types, or API-version migration | Read the relevant reference and the live migration guide |
| Non-Vercel checkout, saved payment methods, or custom payment architecture | Read [references/payments.md](references/payments.md) and current integration-option docs |
| Non-Vercel subscriptions or usage billing | Read [references/billing.md](references/billing.md) and current Billing docs |
| Ordinary Vercel app payment or subscription setup | Use the installed Vercel payments skill |

## Implementation guardrails

- Preserve the repository's existing integration shape unless the user requested a migration.
- Use test mode and non-production fixtures for development whenever practical.
- Keep secret keys server-side and verify webhook signatures.
- Make webhook processing idempotent and resilient to retries and out-of-order delivery.
- Confirm account responsibility, merchant-of-record, fee, refund, dispute, and negative-balance ownership for platform flows.
- Verify regional and account eligibility before proposing Treasury or other availability-limited products.
- Avoid deprecated endpoints only after confirming the supported migration path for the existing integration.

## Handoff

Report the chosen integration route, official documentation checked, existing API/SDK constraints, tests performed, and any migration or production-readiness work that remains.
