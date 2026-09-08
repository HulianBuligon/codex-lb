## Context

PR #1700 intentionally made reset-confirmed warm-up independent of the legacy
exhaustion threshold. The dashboard field remained visible, however, so its
value no longer affected behavior. This change restores the field's contract
while retaining the user's preferred default of warming every confirmed reset.

The warm-up service already receives before/after usage snapshots and the
settings object. Candidate construction is therefore the narrowest ownership
point for applying the threshold consistently to ordinary selected-window
resets and the paid-to-Free fallback.

## Goals / Non-Goals

**Goals:**

- Make the existing threshold effective at the candidate boundary.
- Use `0.0` as the default and accept it through every settings layer.
- Preserve confirmed-reset safety gates and durable deduplication.
- Make the paid-to-Free fallback obey the same operator setting.
- Migrate the old default without overwriting explicit non-default choices.

**Non-Goals:**

- Changing global or per-account warm-up opt-in.
- Changing reset confirmation, availability, cooldown, sender preflight, or
  attempt identity semantics.
- Adding a new public setting, dashboard control, API field, background worker,
  or retry path.

## Decisions

### Apply an inclusive threshold before availability and reset checks

`_build_candidate()` rejects a sample only when `before.used_percent` is below
the configured threshold. The existing `usage_reset_confirmed()` predicate
then remains authoritative for temporal reset evidence. Applying the gate at
this boundary keeps the setting scoped to reset-confirmed warm-up and prevents
it from affecting staggered idle warm-up.

Alternative considered: remove the field or hard-code zero. That would match
the current desired default but leave operators unable to select the previous
strict behavior and would keep the dashboard control misleading.

### Reuse the same gate for paid-to-Free fallback

The paid-to-Free path uses a monthly row that may not have a pre-refresh
sample. Zero permits the confirmed transition without inventing a comparison;
positive values require a real prior monthly sample and apply the same
inclusive comparison. This avoids treating missing evidence as satisfying a
non-zero operator threshold.

### Make zero valid in all settings layers

Backend Pydantic fields use `ge=0`, frontend Zod schemas use `nonnegative()`,
and the numeric control uses `min={0}`. Repository/model defaults and the
active storage server default all use `0.0`, so new settings rows and API/UI
defaults agree.

### Expand active storage with mixed-version synchronization

The migration retains `limit_warmup_exhausted_threshold_percent` and its
`99.0` server default as compatibility storage for replicas running the parent
application schema. It adds `limit_warmup_reset_threshold_percent` with a
`0.0` default. Only a legacy `99.0` row whose optimistic-lock version is still
`1` and whose creation/update timestamps still match is reliably pristine and
maps to `0.0`; a `99.0` row with either evidence of an update is preserved
conservatively, and every non-`99.0` value is copied unchanged.

The ORM keeps the public Python/API attribute on the new column and maps the
old column under an explicit legacy-only attribute. Current writes update both
columns in one optimistic-lock transaction. A positive value is identical in
both; active zero is represented as legacy `99.0` because the parent API
rejects zero. A dialect-specific database trigger handles old replicas that
update only the legacy column: when that value changes and the active value
does not, the trigger copies the new legacy value into active storage. It does
not reinterpret a post-upgrade legacy `99.0`, so an old replica can explicitly
select that threshold.

Downgrade removes the synchronization trigger, copies the latest active value
into legacy storage (`0.0` maps to `99.0`, positive values copy exactly), and
then drops the active column. This preserves the most recent current-replica
write in a representation the parent schema can read.

## Risks / Trade-offs

- [Risk] Existing deployments might have stored `99.0` intentionally. → Only
  a version-1 settings row with equal creation/update timestamps is treated as
  the historical pristine default. Any `99.0` row with evidence of a settings
  update is preserved even when that update was unrelated, favoring operator
  data over an unverifiable default inference.
- [Risk] Old and current replicas may serve concurrently. → Current replicas
  dual-write; a database trigger absorbs legacy-only changes without
  overriding a simultaneous active write; both remain under the existing
  optimistic settings-version contract.
- [Risk] A zero threshold could send more warm-up traffic. → Warm-up remains
  globally and per-account opt-in, post-reset availability-gated, bounded by
  the existing sender/concurrency controls, and deduplicated per reset tuple.
- [Risk] Missing paid-to-Free history could be treated too permissively. →
  Missing history is eligible only at zero; every positive threshold fails
  closed without a prior sample.

## Migration Plan

Apply the new Alembic revision during the normal startup migration. It adds and
backfills active storage using version-based pristine provenance without
mutating the legacy column. During rollout, current replicas dual-write while
the database synchronizes old-replica legacy-only updates into active storage.
Rollback copies active storage into the legacy-compatible representation,
removes synchronization, and then contracts the active column.
