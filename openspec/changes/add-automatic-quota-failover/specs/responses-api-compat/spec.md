## ADDED Requirements

### Requirement: Pre-visible quota failures use bounded account failover

When an otherwise movable Responses request receives a pre-visible upstream
`rate_limit_exceeded`, `usage_limit_reached`, `insufficient_quota`,
`usage_not_included`, or `quota_exceeded` response, and automatic quota
failover is enabled, the proxy MUST release account-local leases, exclude the
rejected account, and select another eligible account using the configured
routing policy. After a replacement is selected, the proxy MUST wait five
seconds before dispatching it. The proxy MUST perform no more than three
additional quota attempts for one request and MUST preserve the existing
overall request deadline. If no replacement is eligible, the proxy MUST
surface the original quota response without the replacement delay.

The behavior MUST apply to streaming HTTP/WebSocket egress and HTTP responses
bridge pre-created requests. It MUST NOT depend on routing strategy,
earlier-reset preference, or transport policy. It MUST NOT replay after an
upstream response event or downstream-visible output, and MUST NOT migrate a
request with uploaded-file, single-account, or other non-reconstructible
account ownership, including a registered durable operation that still requires
its owner. Previous-response and turn-state continuations MAY move
only when the proxy has verified an account-neutral full-history replay:
the replacement MUST omit the old response anchor and account-scoped turn-state
header and MUST NOT reassign stored response or file ownership to the replacement.
HTTP bridge session replacement MUST preserve its existing lease-fenced
continuity cleanup. Old native WebSocket token/history state MUST remain intact.
Disabling automatic quota failover MUST
surface the first qualifying failure without selecting another account.

#### Scenario: Rejected account is excluded and another account completes

- **GIVEN** accounts A and B are eligible for a movable Responses request
- **AND** account A returns `usage_limit_reached` before any response event
- **WHEN** automatic quota failover is enabled
- **THEN** the proxy releases A's request leases and excludes A
- **AND** it selects B through the configured routing policy
- **AND** waits for the bounded delay before dispatching B
- **AND** the client receives B's successful response without A's failure

#### Scenario: No eligible replacement preserves the quota response

- **GIVEN** the selected account returns a qualifying pre-visible quota failure
- **AND** no other account is eligible
- **THEN** the proxy surfaces the original quota response and reset metadata
- **AND** it does not wait for or dispatch a replacement

#### Scenario: Three retries exhaust with the original limit class

- **GIVEN** at least five accounts are otherwise eligible
- **WHEN** the initial account and each replacement returns an explicit
  pre-visible quota failure
- **THEN** the proxy invokes at most four accounts total
- **AND** waits before each of the three replacement attempts
- **AND** surfaces the final quota failure without selecting a fifth account

#### Scenario: Disabled setting surfaces without account failover

- **GIVEN** automatic quota failover is disabled
- **WHEN** the selected account returns a qualifying pre-visible quota failure
- **THEN** the proxy surfaces that failure
- **AND** it does not select another account for that failure

#### Scenario: Generic failure keeps the existing retry budget

- **WHEN** an upstream request fails with a code outside the quota allowlist
- **THEN** the failure does not expand or consume the quota retry budget
- **AND** existing failure classification and retry limits remain authoritative

#### Scenario: Hard continuity remains fail-closed

- **GIVEN** a request requires a previous-response, turn-state, uploaded-file,
  single-account, or other hard account owner
- **AND** an account-neutral full-history replay cannot be verified
- **WHEN** that owner returns a qualifying quota failure
- **THEN** the proxy does not send the request to another account
- **AND** it surfaces the owner-unavailable or upstream quota terminal defined
  by the existing continuity contract

#### Scenario: Verified continuation recovers after quota rejection

- **GIVEN** a continuation has a verified, self-contained full-history replay
- **AND** no registered durable operation or other non-reconstructible
  account ownership requires its original owner
- **AND** its owner rejects it with an explicit quota code before acceptance
- **WHEN** automatic quota failover is enabled
- **THEN** the proxy retries the full history on another eligible account
- **AND** the old response id and turn-state token do not cross accounts
- **AND** the same three-retry ceiling, delay, and request deadline apply
- **AND** unrelated sticky mappings and old response ownership remain intact

#### Scenario: Visible response is not replayed

- **GIVEN** upstream has emitted a response event or output is downstream-visible
- **WHEN** a quota terminal arrives
- **THEN** the proxy does not replay the request on another account
- **AND** it surfaces the terminal in the existing response lifecycle
