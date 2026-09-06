## ADDED Requirements

### Requirement: Reset warm-up threshold default is all-resets

The `dashboard_settings` table MUST include a non-null Float column named
`limit_warmup_exhausted_threshold_percent` whose server default is `0.0`. The
upgrade migration MUST convert existing rows whose value is exactly the
historical default `99.0` to `0.0`, while preserving other configured values.

#### Scenario: New settings rows use zero threshold

- **WHEN** a dashboard settings row is created after the migration
- **THEN** `limit_warmup_exhausted_threshold_percent` defaults to `0.0`

#### Scenario: Historical default is migrated

- **GIVEN** an existing dashboard settings row has
  `limit_warmup_exhausted_threshold_percent = 99.0`
- **WHEN** the migration is applied
- **THEN** the stored value becomes `0.0`

#### Scenario: Explicit threshold is preserved

- **GIVEN** an existing dashboard settings row has a threshold other than
  `99.0`
- **WHEN** the migration is applied
- **THEN** the stored value remains unchanged

#### Scenario: Zero is accepted by the settings contract

- **WHEN** the settings API receives
  `limitWarmupExhaustedThresholdPercent = 0`
- **THEN** the update is accepted and persisted
