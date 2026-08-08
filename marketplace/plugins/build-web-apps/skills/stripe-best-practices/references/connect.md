# Connect / Platforms

Verify every endpoint, field, and recommendation against the current official Stripe Connect documentation before implementation. This reference records decision dimensions, not a frozen API contract.

## Table of contents
- Current account API
- Controller properties
- Charge types
- Integration guides

## Current account API

For a new platform, start from Stripe's current [Connect overview](https://docs.stripe.com/connect.md) and account-creation guidance. Confirm which account API and configuration model Stripe currently recommends for the platform's country, capabilities, and responsibility model.

Do not migrate an existing account integration merely because a newer API exists. Review Stripe's migration guidance, pinned API version, stored account identifiers, onboarding flow, and webhook contract first.

## Controller properties

When the current account API exposes controller or responsibility properties, use them to make the platform's obligations explicit:

| Property | Controls |
|---|---|
| `controller.losses.payments` | Who is liable for negative balances |
| `controller.fees.payer` | Who pays Stripe fees |
| `controller.stripe_dashboard.type` | Dashboard access (`full`, `express`, `none`) |
| `controller.requirement_collection` | Who collects onboarding requirements |

Confirm the current property names and combinations in Stripe's live connected-account configuration documentation before writing code.

Always describe accounts in terms of their responsibility settings, dashboard access, and [capabilities](https://docs.stripe.com/connect/account-capabilities.md) to describe what connected accounts can do.

When reviewing a legacy integration that uses bundled account types, describe the actual responsibility, dashboard, requirement-collection, and capability choices instead of assuming the label alone defines behavior.

## Charge types

Choose one charge type per integration — do not mix them. For most platforms, start with destination charges:

- **Destination charges** — Use when the platform accepts liability for negative balances. Funds route to the connected account via `transfer_data.destination`.
- **Direct charges** — Use when the platform wants Stripe to take risk on the connected account. The charge is created on the connected account directly.

Use `on_behalf_of` to control the merchant of record, but only after reading [how charges work in Connect](https://docs.stripe.com/connect/charges.md).

**Traps to avoid:** Do not use the Charges API for Connect fund flows — use PaymentIntents or Checkout Sessions with `transfer_data` or `on_behalf_of`. Do not mix charge types within a single integration.

## Integration guides

- [SaaS platforms and marketplaces guide](https://docs.stripe.com/connect/saas-platforms-and-marketplaces.md) — Choosing the right integration shape.
- [Interactive platform guide](https://docs.stripe.com/connect/interactive-platform-guide.md) — Step-by-step platform builder.
- [Design an integration](https://docs.stripe.com/connect/design-an-integration.md) — Detailed risk and responsibility decisions.
