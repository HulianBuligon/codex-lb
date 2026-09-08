## MODIFIED Requirements

### Requirement: Limit warm-up persistence

The database SHALL persist global warm-up settings, per-account opt-in,
warm-up attempt history, and request-log source metadata. During the
expand/contract rollout, global settings SHALL retain the non-null legacy
`limit_warmup_exhausted_threshold_percent` column with its `99.0` server
default for replicas running the previous application schema. The database
SHALL also include a non-null active
`limit_warmup_reset_threshold_percent` Float column with a `0.0` server
default; the current application SHALL expose that active value through the
existing `limit_warmup_exhausted_threshold_percent` settings contract.

The upgrade migration SHALL copy each legacy value into the active column,
except that the historical `99.0` default SHALL become the new `0.0` default.
It MUST NOT rewrite the legacy column or its server default. Downgrade SHALL
remove only the active column so the previous application schema can continue
to read every legacy row.

#### Scenario: Warm-up attempt is unique per reset

- **WHEN** an attempt is stored for an account, window, and reset timestamp
- **THEN** the database enforces uniqueness for that account/window/reset tuple

#### Scenario: Existing installs remain disabled

- **WHEN** an existing database is migrated
- **THEN** global warm-up is disabled
- **AND** all existing accounts remain opted out
- **AND** the legacy exhausted-threshold percent keeps its existing value and
  `99.0` server default
- **AND** the active reset-threshold percent has a `0.0` server default

#### Scenario: Historical default is expanded without mutating legacy data

- **GIVEN** an existing dashboard settings row has legacy
  `limit_warmup_exhausted_threshold_percent = 99.0`
- **WHEN** the migration is applied
- **THEN** `limit_warmup_reset_threshold_percent` is `0.0`
- **AND** the legacy value and its `99.0` server default remain unchanged

#### Scenario: Explicit threshold is copied into active storage

- **GIVEN** an existing dashboard settings row has a legacy threshold other
  than `99.0`
- **WHEN** the migration is applied
- **THEN** the active reset-threshold value equals that configured value
- **AND** the legacy value remains unchanged

#### Scenario: Zero is persisted only in active storage

- **WHEN** the settings API receives
  `limitWarmupExhaustedThresholdPercent = 0`
- **THEN** the update is accepted and persisted in
  `limit_warmup_reset_threshold_percent`
- **AND** the compatibility-only legacy column remains readable by previous
  replicas

#### Scenario: Downgrade preserves the previous application contract

- **GIVEN** the active reset-threshold column was added by this change
- **WHEN** the migration is downgraded to its parent revision
- **THEN** `limit_warmup_reset_threshold_percent` is removed
- **AND** `limit_warmup_exhausted_threshold_percent` retains its prior value
  and `99.0` server default

#### Scenario: Warm-up request logs remain separable from user traffic

- **WHEN** a warm-up request is logged
- **THEN** the request log records a source value that allows account usage
  summaries to exclude internal warm-up traffic
