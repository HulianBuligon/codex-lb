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
except that a historical `99.0` default with
`dashboard_settings.version = 1` and `created_at = updated_at` SHALL become the
new `0.0` default. A legacy `99.0` with either evidence of an update SHALL
remain `99.0`. Upgrade MUST NOT rewrite the legacy column or its server
default.

During mixed-version operation, the current application SHALL write both
columns in one settings update. Positive active values SHALL use the same
legacy value, while active `0.0` SHALL use legacy `99.0`. A legacy-only update
that changes the legacy value without changing the active value SHALL copy the
new legacy value into active storage. Downgrade SHALL copy the latest active
value back into legacy storage, representing active `0.0` as legacy `99.0`,
before it removes the active column.

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

#### Scenario: Pristine historical default is expanded without mutating legacy data

- **GIVEN** an existing dashboard settings row has legacy
  `limit_warmup_exhausted_threshold_percent = 99.0`
- **AND** its settings version is `1`
- **AND** its creation and update timestamps are equal
- **WHEN** the migration is applied
- **THEN** `limit_warmup_reset_threshold_percent` is `0.0`
- **AND** the legacy value and its `99.0` server default remain unchanged

#### Scenario: Configured 99 percent is preserved

- **GIVEN** an existing dashboard settings row has legacy
  `limit_warmup_exhausted_threshold_percent = 99.0`
- **AND** its settings version is greater than `1` or its creation and update
  timestamps differ
- **WHEN** the migration is applied
- **THEN** `limit_warmup_reset_threshold_percent` is `99.0`
- **AND** the legacy value remains unchanged

#### Scenario: Explicit threshold is copied into active storage

- **GIVEN** an existing dashboard settings row has a legacy threshold other
  than `99.0`
- **WHEN** the migration is applied
- **THEN** the active reset-threshold value equals that configured value
- **AND** the legacy value remains unchanged

#### Scenario: Current replica dual-writes a positive threshold

- **WHEN** the settings API receives
  `limitWarmupExhaustedThresholdPercent = 50`
- **THEN** both threshold columns persist `50.0`

#### Scenario: Zero uses a legacy-compatible representation

- **WHEN** the settings API receives
  `limitWarmupExhaustedThresholdPercent = 0`
- **THEN** the update is accepted and persisted in
  `limit_warmup_reset_threshold_percent`
- **AND** the compatibility-only legacy column persists `99.0`

#### Scenario: Legacy-only mixed-version write updates active storage

- **GIVEN** the expand migration is active
- **WHEN** a previous replica changes only
  `limit_warmup_exhausted_threshold_percent`
- **THEN** `limit_warmup_reset_threshold_percent` is set to that same value

#### Scenario: Downgrade preserves the previous application contract

- **GIVEN** the active reset-threshold column was added by this change
- **AND** its latest value differs from the compatibility column
- **WHEN** the migration is downgraded to its parent revision
- **THEN** `limit_warmup_reset_threshold_percent` is removed
- **AND** a positive active value is copied exactly into
  `limit_warmup_exhausted_threshold_percent`
- **AND** an active `0.0` is represented there as `99.0`
- **AND** the legacy `99.0` server default remains unchanged

#### Scenario: Warm-up request logs remain separable from user traffic

- **WHEN** a warm-up request is logged
- **THEN** the request log records a source value that allows account usage
  summaries to exclude internal warm-up traffic
