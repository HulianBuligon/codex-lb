## 1. Threshold behavior

- [x] 1.1 Pass the configured threshold into ordinary reset-confirmed candidate
  construction.
- [x] 1.2 Enforce the inclusive pre-reset comparison and keep reset confirmation
  and post-reset availability checks unchanged.
- [x] 1.3 Apply the same threshold semantics to paid-to-Free monthly fallback
  candidates.

## 2. Settings and migration

- [x] 2.1 Change repository, ORM, and API defaults/validation to allow `0.0`,
  while mapping the public setting to active storage and dual-writing a
  legacy-compatible value into the previous column.
- [x] 2.2 Add an expand/contract Alembic migration that maps a historical
  `99.0` default to `0.0` only for a pristine version-1 settings row with
  matching creation/update timestamps, preserves configured `99.0`, copies
  other values, and leaves the legacy column intact.
- [x] 2.3 Update frontend schemas, numeric bounds, fixtures, and translated
  descriptions.
- [x] 2.4 Synchronize legacy-only mixed-version writes into active storage and
  copy the latest active value back to the legacy representation on downgrade.

## 3. Regression coverage

- [x] 3.1 Prove the zero default warms a reset after non-exhausted prior usage.
- [x] 3.2 Prove a positive threshold skips below-threshold usage and accepts
  the inclusive boundary.
- [x] 3.3 Prove paid-to-Free fallback respects positive thresholds and zero
  threshold behavior.
- [x] 3.4 Cover API dual-write, migration provenance, legacy-only mixed-version
  writes, downgrade preservation, frontend schema, and component contracts.

## 4. Verification

- [x] 4.1 Run focused backend tests, Ruff, and diff hygiene checks.
- [x] 4.2 Run frontend lint, typecheck, and focused Vitest coverage.
- [x] 4.3 Validate the OpenSpec change strictly and verify a clean upstream
  patch application.
- [x] 4.4 Re-run focused and full validation after mixed-version review fixes.
