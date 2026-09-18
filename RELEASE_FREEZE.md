# ShopProject — Phase D Release / Freeze

Phase D contains the final three release steps.

## D1 — Production Preparation
- Confirm frontend production build is green.
- Confirm Django migrations are clean (`makemigrations --check` already verified before Phase D).
- Review production environment values: DEBUG, ALLOWED_HOSTS, CORS, CSRF trusted origins, refresh-cookie security.
- Confirm secrets are supplied through environment configuration, not source control.

## D2 — Cleanup / Documentation
- Remove temporary/debug artifacts and obsolete phase-only notes where safe.
- Keep business rules and security decisions documented.
- Preserve the frozen 15-step roadmap.
- Do not alter business logic during cleanup.

## D3 — Final Freeze
- Phase A: 5/5 green.
- Phase B: 4/4 green.
- Phase C: 3/3 green.
- Total: 12 completed validation steps across A-C; Phase D completes the release/freeze checklist.
- No new phase or step is to be opened unless a real regression is discovered.

## Final verification policy
Do not rerun the full backend suite merely for the freeze. Use the already completed green results and the final frontend build result. Run additional tests only if a release-only change introduces a concrete regression risk.
