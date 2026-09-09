## Goals / Non-Goals

**Goals:**

- Recover a safe request automatically when one selected account has no usable
  quota and another eligible account can serve it.
- Preserve cache locality until the owner explicitly proves exhausted.
- Make unattended recovery bounded and operator-disableable.
- Apply the same contract across normal streaming and HTTP bridge egress.

**Non-Goals:**

- No replay after response acceptance or downstream-visible output.
- No migration of files, incomplete/account-scoped history, or durable operations
  that require their original owner. An existing verified account-neutral full
  history may replace its continuation anchor before acceptance.
- No changes to account ranking, quota estimation, reset ordering, or routing
  strategy semantics.
- No retry of arbitrary upstream or local failures.
- No configurable retry count or delay; both remain conservative internal
  constants to avoid adding setup surface.

## Decisions

- **Use a narrow normalized-code allowlist.** Quota failover is authorized only
  by explicit upstream limit codes. This avoids converting generic failure
  handling into an account probe loop.
- **Give quota failure its own retry counter.** The request may make three
  additional quota attempts even though the pre-existing generic account
  attempt budget is smaller. The outer streaming iterator expands only after a
  qualifying quota failure, so non-quota behavior retains its old budget.
- **Delay each selected account handoff by five seconds.** Replacement
  selection happens first, then the delay limits rapid account probing and
  gives upstream/account state time to settle before dispatch. An empty
  replacement pool surfaces the original quota response immediately. Tests
  use the scheduler seam or a patched constant rather than wall-clock waiting.
- **Exclude before selecting.** The failed account id enters the request-local
  exclusion set before another selection. The current routing strategy then
  ranks the remaining candidates normally.
- **Retire only soft exhaustion affinity.** `usage_limit_reached`,
  `insufficient_quota`, `usage_not_included`, `quota_exceeded`, and a
  `rate_limit_exceeded` message that explicitly names quota/usage exhaustion
  can clear a prompt-cache or sticky-thread owner with compare-and-set. Hard
  session kinds are never cleared by this path.
- **Keep a persisted default-on kill switch.** The feature is zero-config and
  fixes unattended operation by default. The switch is an operational escape
  hatch because retrying external calls is materially different from merely
  rendering data; operators can disable it without rebuilding or restarting.
- **Share retry constants across transports.** Streaming and bridge paths use
  the same error allowlist, three-retry ceiling, and five-second delay so
  transport configuration cannot change the contract.
- **Detach verified continuation bodies, not arbitrary ownership.** Reuse the
  retained full-history proof and account-neutral validator. On quota only,
  release the request's obsolete response/turn-state pin and select without
  that hard affinity. Clear the old transport/session headers before dispatch.
  Native WebSocket recovery uses a separate in-memory continuity state so a
  new response does not overwrite the old token's cached history. Bridge
  recovery uses its existing lease-fenced reconnect and continuity cleanup;
  requests with a durable operation id remain owner-bound. The kill switch,
  single-account strategy, output visibility, pending siblings, file pins,
  and unchanged request deadline remain authoritative.

## Migration

The Alembic revision adds a non-null boolean column with a true server default.
Existing rows become enabled during upgrade, old application replicas ignore
the additive column, and current replicas persist the value through the
settings API. Downgrade drops only the new preference column.

The no-op `20260909_080000_merge_quota_failover_upstream` revision joins the
quota-setting branch with upstream's `20260909_070000_automation_run_claim_budget`.
Neither existing migration is rewritten; databases already on either branch
can upgrade to one head, and merge downgrade restores both parent stamps.

## Risks / Trade-offs

- Up to three rejected attempts add at most fifteen seconds before a terminal
  failure, subject to the existing overall request deadline.
- A broad upstream `rate_limit_exceeded` code can represent temporary rate
  pressure rather than exhausted usage. It qualifies for failover, but its soft
  sticky owner is retired only when the accompanying message explicitly says
  usage limit or quota.
- Retiring a soft owner can reduce cache hits for later requests on that key;
  keeping an owner that has explicitly exhausted usage would instead wedge
  those requests, so the targeted loss of locality is intentional.
