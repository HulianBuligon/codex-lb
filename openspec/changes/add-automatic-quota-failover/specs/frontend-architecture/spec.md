## ADDED Requirements

### Requirement: Routing settings expose automatic quota failover

The dashboard Routing settings section SHALL expose an accessible switch for
`quotaFailoverEnabled`. The setting SHALL default to enabled when omitted from
a mixed-version payload, SHALL save through the existing settings API, and
SHALL explain that explicit quota-limit responses can be retried on another
eligible account up to three additional times. The label, description, and
accessible name MUST exist in English, Korean, and Simplified Chinese locale
bundles.

#### Scenario: Operator disables automatic quota failover

- **GIVEN** the Routing settings section shows automatic quota failover enabled
- **WHEN** the operator activates the switch
- **THEN** the dashboard sends `quotaFailoverEnabled: false` through the
  settings API
- **AND** the saved state renders disabled

#### Scenario: Mixed-version response receives safe default

- **WHEN** a dashboard settings response omits `quotaFailoverEnabled`
- **THEN** the frontend schema resolves it to enabled
