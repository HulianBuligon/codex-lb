## 1. Contract

- [x] 1.1 Define the explicit quota-code allowlist, pre-visible replay boundary,
  three-retry/five-second limits, and account exclusion behavior.
- [x] 1.2 Define soft-affinity retirement and hard-continuity preservation.
- [x] 1.3 Define the default-on persisted kill switch and routing UI behavior.
- [x] 1.4 Define additive migration and downgrade behavior.

## 2. Implementation

- [x] 2.1 Add bounded quota failover to streaming Responses requests without
  widening the generic retry budget.
- [x] 2.2 Add the same exclusion and retry budget to direct WebSocket and HTTP
  bridge pre-created requests.
- [x] 2.3 Retire only exhausted soft sticky owners with compare-and-set.
- [x] 2.4 Persist `quota_failover_enabled` and expose it through settings API,
  cache, frontend schema, payload, switch, mocks, and locales.

## 3. Coverage

- [x] 3.1 Cover HTTP and serialized-SSE quota responses, account exclusion,
  three retries, kill-switch behavior, and soft-pin safety.
- [x] 3.2 Cover direct WebSocket and HTTP bridge success, three-retry ceiling,
  disabled behavior, and deadline safety.
- [x] 3.3 Cover settings default/persistence, frontend parsing/render/save, and
  audit changed fields.
- [x] 3.4 Cover migration upgrade, defaulted existing row, downgrade,
  re-upgrade, single-head graph, and schema drift.

## 4. Verification

- [x] 4.1 Run focused proxy, settings, frontend, and migration tests.
- [x] 4.2 Run backend/frontend lint, typecheck, build, and relevant regression
  suites.
- [x] 4.3 Validate this change strictly and validate all canonical specs.
- [x] 4.4 Capture before/after dashboard evidence and proxy output evidence.
- [x] 4.5 Review the final consolidated diff once before publication.

## 5. Publication

- [x] 5.1 Push the feature branch to the contributor fork and open a PR against
  `Soju06/codex-lb:main` using the repository template.
