# Treasury / Financial Accounts

Treasury and financial-account availability, naming, and API surfaces can change by account and region. Verify current eligibility and official documentation before recommending or implementing a route.

## Table of contents
- Current financial-account route
- Existing integrations

## Current financial-account route

For embedded financial accounts, account and routing details, or money movement, begin with the current [Treasury overview](https://docs.stripe.com/treasury.md). Confirm product eligibility, supported countries, account requirements, and Stripe's currently recommended API before writing code.

Document the intended fund flow, ownership, reconciliation, compliance responsibilities, and webhook lifecycle before selecting endpoints.

## Existing integrations

Do not upgrade or replace an existing Treasury API surface implicitly. Inspect its pinned API version and current behavior, then use Stripe's live migration guidance to determine whether a migration is supported and worthwhile.
