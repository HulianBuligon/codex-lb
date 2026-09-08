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
maps a legacy `99.0` to `0.0` only when `dashboard_settings.version = 1` and
`created_at = updated_at` jointly identify a pristine settings row, and copies
every other stored percentage. A `99.0` row with either evidence of an update
is conservatively preserved as an explicit choice because migration-time data
cannot distinguish a threshold edit from an unrelated settings edit.

The current application exposes the new column through the existing public
setting name and dual-writes the compatibility column. Positive values are
stored identically in both columns; active `0.0` uses legacy `99.0`, which the
previous positive-only schema can read. A database trigger copies a changed
legacy value into active storage only when the same statement did not change
the active value, allowing old replicas to participate without overriding a
new replica's dual-write. Downgrade first maps the latest active value back to
legacy storage (`0.0` becomes `99.0`; positive values remain unchanged), then
removes the trigger and active column.
