# Gemini work package 01 — frontend contract hardening

Scope: `frontend/` only. Do not edit Python, backend contracts, repository identity, or Git history.
Do not add `node_modules/` or `dist/` to version control. Complete the tasks in order and keep each
change mechanical and test-backed.

## Task 1: make scan results match the backend exactly

Define and use this concrete successful job result instead of inspecting several guessed keys:

```ts
type ScanErrorSample = { path: string; message: string };
type ScanJobResult = {
  discovered: number;
  added: number;
  updated: number;
  unchanged: number;
  errors: number;
  embedded: number;
  missing: number;
  error_samples: ScanErrorSample[];
};
```

Update `LibraryScanContext` and `LibrarySetup` to show the counters and render each sampled error's
path and message. Do not look for `sampled_errors`, and do not treat the numeric `errors` field as an
array. Add tests for a successful scan with samples and a failed job with `Job.error`.

## Task 2: verify every API state

For the centralized API client, add or retain tests covering:

- 202 scan acceptance and job polling through queued → running → succeeded
- `409 scan_already_running`, resuming from `error.details.job_id`
- `409 library_not_indexed`, navigating the user to library setup
- 422 validation envelope and generic 500 envelope
- an empty playlist and a playlist shorter than the requested size
- 202 feedback without optimistic retry duplication

Use the shapes in `docs/FRONTEND_HANDOFF.md`; do not invent new endpoints.

## Task 3: harden playback without changing its design

Keep exactly one root-mounted `<audio>` element. Verify with tests that next/previous, seek, skip
feedback, queue replacement, and track removal do not create additional audio elements. Handle 404
and 410 playback failures with a visible notification and advance safely to the next playable item.
Use `audio_url` verbatim; never construct a filesystem path.

## Task 4: development configuration and accessibility

- Use one `VITE_API_BASE_URL` setting, defaulting to the same origin; keep the Vite development
  proxy pointed at `http://127.0.0.1:8000`.
- Ensure controls have accessible names, keyboard focus is visible, progress has appropriate ARIA
  values, notifications are announced, and icon-only buttons have labels.
- Preserve the existing visual direction. Do not redesign the application.

## Task 5: clean delivery

- Update `frontend/README.md` with exact install, dev, test, and build commands.
- Run `npm test` and `npm run build`.
- Write `frontend/HANDOFF_RESULT.md` listing changed files, commands run, test/build results, and any
  remaining backend dependency. Do not claim completion without actual command output.

Acceptance: all frontend tests pass, production build succeeds, no generated dependency/build
folders are staged, and no backend files are changed.

