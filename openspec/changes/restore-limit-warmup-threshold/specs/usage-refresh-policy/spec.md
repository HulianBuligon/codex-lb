## MODIFIED Requirements

### Requirement: Reset-confirmed limit warm-up

The system SHALL support an optional limit warm-up mechanism that is disabled
by default. When enabled globally and for an account, background usage refresh
MAY send one minimal upstream Responses request after it confirms that a
selected quota window has moved into a newly available reset window. The
pre-reset usage gate SHALL be configurable through
`limit_warmup_exhausted_threshold_percent`, SHALL use an inclusive comparison
(`before.used_percent >= threshold`), and SHALL default to `0.0` percent. A
zero threshold SHALL qualify every confirmed reset; a positive threshold SHALL
require the observed pre-reset sample to meet that floor. Existing post-reset
availability, opt-in, active-account, sender, and durable deduplication gates
remain required.

#### Scenario: Zero threshold warms a non-exhausted confirmed reset

- **GIVEN** limit warm-up is enabled globally and for an account
- **AND** `limit_warmup_exhausted_threshold_percent` is `0.0`
- **AND** the account's previous usage sample for a selected window was `15%`
- **WHEN** background usage refresh records a newer sample for that window with
  `used_percent < 100` and a confirmed later `reset_at`
- **THEN** the system sends at most one warm-up request for that
  account/window/reset tuple

#### Scenario: Positive threshold skips a below-threshold reset

- **GIVEN** limit warm-up is enabled globally and for an account
- **AND** `limit_warmup_exhausted_threshold_percent` is `50.0`
- **AND** the account's previous usage sample for a selected window was `15%`
- **WHEN** background usage refresh records a newer sample for that window with
  `used_percent < 100` and a confirmed later `reset_at`
- **THEN** background usage refresh MUST NOT send warm-up traffic for that
  window

#### Scenario: Threshold comparison is inclusive

- **GIVEN** limit warm-up is enabled globally and for an account
- **AND** `limit_warmup_exhausted_threshold_percent` is `50.0`
- **AND** the account's previous usage sample for a selected window was exactly
  `50%`
- **WHEN** background usage refresh records a newer sample for that window with
  `used_percent < 100` and a confirmed later `reset_at`
- **THEN** the system sends at most one warm-up request for that
  account/window/reset tuple

#### Scenario: Paid-to-Free fallback applies the same threshold

- **GIVEN** an opted-in paid account is confirmed as `free` during a usage
  refresh
- **AND** the refresh writes a fresh available monthly usage row
- **AND** `limit_warmup_exhausted_threshold_percent` is greater than `0.0`
- **AND** no pre-refresh monthly sample exists or that sample is below the
  configured threshold
- **THEN** background usage refresh MUST NOT send the transition warm-up
- **AND WHEN** the threshold is `0.0`
- **THEN** the confirmed transition MAY send one monthly warm-up

#### Scenario: Warm-up is skipped unless reset is confirmed

- **GIVEN** limit warm-up is enabled globally and for an account
- **AND** the pre-reset sample meets the configured threshold
- **WHEN** the newer sample does not prove a real reset transition
- **THEN** background usage refresh MUST NOT send warm-up traffic

#### Scenario: Warm-up is not triggered by upstream reset_at timestamp jitter

- **GIVEN** limit warm-up is enabled globally and for an account
- **AND** the account's previous usage sample meets the configured threshold
- **WHEN** background usage refresh records a newer sample whose `reset_at`
  advanced by less than 60 seconds (upstream timestamp jitter)
- **THEN** the system MUST NOT send a warm-up request for that
  account/window/reset tuple

#### Scenario: Warm-up is opt-in and safe by default

- **GIVEN** background usage refresh is preparing to evaluate limit warm-up
  candidates
- **WHEN** global limit warm-up is disabled
- **OR** the account is not opted in
- **THEN** background usage refresh MUST NOT send warm-up traffic

#### Scenario: Warm-up uses fresh opt-in state after usage refresh

- **GIVEN** an account was loaded before a background usage refresh cycle
- **AND** the account's limit warm-up opt-in changes while the refresh cycle is
  running
- **WHEN** the scheduler evaluates warm-up candidates after writing usage
  samples
- **THEN** the scheduler MUST evaluate the latest persisted opt-in value rather
  than the stale in-session account object

#### Scenario: Warm-up respects unsafe account states

- **WHEN** an account is paused, deactivated, rate-limited, quota-exceeded, or
  in an auth-refresh failure path
- **THEN** limit warm-up MUST NOT send traffic for that account

#### Scenario: Warm-up attempts are durable and deduplicated

- **WHEN** multiple refresh workers observe the same account/window/reset
  candidate
- **THEN** the database permits at most one persisted attempt for that tuple
- **AND** later refresh cycles skip that tuple after a prior attempt exists

#### Scenario: Staggered idle warm-up pre-starts rolling primary windows

- **GIVEN** limit warm-up and staggered idle warm-up are enabled globally
- **AND** multiple active accounts are opted into limit warm-up
- **AND** an opted-in account has a healthy idle short-window primary usage
  sample (any sample reporting a duration over 24 hours is not eligible) with
  `used_percent` at or below the configured
  `limit_warmup_idle_threshold_percent`
- **AND** no prior warm-up attempt places the account inside the configured
  cooldown
- **AND** the usage sample was refreshed for the current cycle
- **WHEN** background usage refresh evaluates that account inside its
  deterministic stagger slot
- **THEN** the system MUST attempt to send one minimal upstream warm-up request
  for that account's current rolling-window cycle, whose length is the
  account's observed primary window duration (defaulting to 300 minutes when
  duration metadata is missing)
- **AND** the system MUST NOT send another staggered idle warm-up for that same
  account/cycle tuple
- **AND** account slots MUST be spread deterministically across the account's
  rolling window so restarts do not align all opted-in accounts into the same
  phase

#### Scenario: Staggered idle warm-up is skipped for accounts with real usage

- **GIVEN** staggered idle warm-up is enabled globally
- **AND** an active opted-in account has a short-window primary usage sample
  with `used_percent` above the configured
  `limit_warmup_idle_threshold_percent`
- **WHEN** background usage refresh evaluates that account
- **THEN** the system MUST NOT send staggered idle warm-up traffic for that
  account

#### Scenario: Staggered idle warm-up remains opt-in

- **GIVEN** limit warm-up is enabled globally and for an account
- **AND** staggered idle warm-up is disabled
- **WHEN** background usage refresh observes an idle short-window primary
  sample that is not a reset-confirmed transition
- **THEN** limit warm-up MUST NOT send synthetic traffic for that idle sample
