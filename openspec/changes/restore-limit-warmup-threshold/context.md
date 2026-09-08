## Decision

The predicate is inclusive: a reset-confirmed candidate qualifies when the
pre-refresh usage is greater than or equal to the configured percentage. The
setting is therefore a meaningful range rather than an on/off switch:

| Setting | Eligibility |
| --- | --- |
| `0%` | every confirmed reset, including a `15% -> 0%` reset |
| `50%` | only resets whose previous sample was at least `50%` used |
| `99%` | only practically exhausted resets at or above `99%` |
| `100%` | only fully exhausted resets |

The default is intentionally `0%` because the operator's desired behavior is
to warm every confirmed reset. A default of `100%` would mean almost the
opposite: it would skip resets whose previous sample was below full exhaustion.

## Safety boundaries

The threshold is only one eligibility gate. Existing reset confirmation,
post-reset availability, global/account opt-in, account-active, model
eligibility, cooldown, and durable account/window/reset deduplication remain
unchanged. The threshold does not make an unconfirmed or exhausted post-reset
sample eligible.

For a paid-to-Free transition, upstream can replace the paid window with a
fresh monthly row and there may be no comparable pre-refresh monthly sample.
The default zero threshold treats the confirmed transition as eligible. A
positive threshold fails closed until a pre-refresh monthly sample exists and
meets the configured floor.

## Migration behavior

The original threshold migration created
`limit_warmup_exhausted_threshold_percent` with `99.0` as the server default.
That column must remain unchanged while old replicas may still serve traffic.
The expand/contract migration therefore adds
`limit_warmup_reset_threshold_percent` as the active `0.0`-default storage,
maps legacy `99.0` rows to `0.0`, and copies every other stored percentage.
The current application exposes the new column through the existing public
setting name. Downgrade drops only the new column, leaving the old schema and
data readable.
