# Chipping Roadmap

This is the working backlog for the deployed app at `chip.cashbaggins.dev`.

The V0 app is live and usable. `docs/SPEC.md` remains the product behavior reference, while this file tracks the next practical work from the current deployed state.

## Current State

Implemented and deployed:

- Observer Mode public dashboard.
- Owner login / Me Mode.
- Manual practice sessions.
- Quick Log with bucket and partial-bucket support.
- Target Completion sequential 1-9 and random 1-9.
- Target Completion miss, hit, undo, retrieve/end bucket, and stop-game flow.
- Public read-only stats endpoints.
- Owner CSV and JSON export.
- Owner prompt helper.
- Docker Compose deployment with Postgres and Cloudflare Tunnel.
- Build/session provenance fields and session-level code links.
- Real target-net dashboard visual with range filters and last-run mode.
- App-era badges, visual era snapshots, and a compact App Evolution timeline.

## Immediate Next Work

### 1. Play Data Pass

Do 1-3 real Target Completion runs before making the next analytics decisions.

Use the data to evaluate:

- Whether `30D` should remain the dashboard default.
- Whether `Last Run` is the right second target-map mode.
- Whether target labels, attempt counts, and empty states are too loud or too quiet.
- Whether the public dashboard encourages the right practice behavior.

This is not a code milestone by itself. It is a calibration pass before the next visual iteration.

### 2. Reuse The Net Map In Practice Views

The public dashboard now has the best target visual. The owner workflow and session detail should use the same visual language.

Targets:

- Add a session-level net map to session detail.
- Replace or augment the active Me Mode Target Completion target grid with a compact net map.
- Highlight current target, completed targets, and per-target attempts.
- Keep Me Mode fast and clear; the visual should support logging, not slow it down.

Recommended scope:

- Reuse the existing frontend layout data.
- Avoid new backend tables.
- Use existing session/game payloads where possible.

### 3. Session Detail Polish

Make individual sessions feel portfolio-readable and useful for review.

Potential improvements:

- Stronger session summary header.
- Better Target Completion run recap.
- Bucket timeline polish.
- Session-level target map.
- Clear code/provenance card that feels integrated rather than technical-only.

This should come after at least one new Target Completion session so the design can be judged with real data.

## Analytics Backlog

### Target Trend Mode

Add a third target-map mode for recent performance versus baseline.

Useful comparisons:

- `Last session` versus `All`.
- `7D` versus `All`.
- `30D` versus `All`.

Questions it should answer:

- Which targets are improving?
- Which targets are regressing?
- Which targets are under-sampled?

Important rule:

- Do not overstate trends from tiny sample sizes. Low-sample targets should be visually muted or marked as low confidence.

### Completion Trend Depth

Improve Target Completion analytics once more runs exist.

Potential metrics:

- Best score.
- Median score.
- Recent score trend.
- Sequential versus random comparison.
- Time to complete.
- Balls used by target over recent completed runs.

### Practice History Drilldowns

Add more ways to inspect history after enough data exists.

Potential views:

- Session list filtering.
- Target-specific history.
- Club/distance summaries.
- Volume consistency.
- Best/worst sessions.

## Provenance And Portfolio Backlog

### App Era Timeline

The first lightweight version is implemented. The app records build/session provenance and now exposes it as quiet product-history metadata.

Implemented:

- Define named app eras.
- Show which era each session belongs to.
- Link sessions to the code SHA recorded when they were created.
- Add a small public timeline of meaningful app improvements.
- Show small visual snapshots for each era.

Future refinements:

- Replace representative UI snapshots with captured bitmap screenshots if the difference matters.
- Historical UI replay or versioned presentation components.

### Portfolio Presentation

Keep improving the public side as a polished training dashboard with subtle portfolio value.

Direction:

- Make facts immediately interpretable.
- Prefer dense, purposeful visuals over marketing sections.
- Keep portfolio hints subtle: build links, app-era notes, and session provenance.

Avoid:

- Decorative charts that do not answer a practice question.
- Public copy that explains how to use the app instead of showing the data.

## CV Foundation Backlog

This remains deferred. Do not implement actual computer vision until the lightweight foundation is intentionally scheduled.

Foundation scope:

- Add a `cv_events` table/model/migration.
- Add `CV_WORKER_API_KEY`.
- Add `GET /api/cv/active-context`.
- Add `POST /api/cv/events`.
- Add `GET /api/cv/events/recent`.
- Require owner auth or the CV worker API key.
- Add an owner-only CV debug page.
- Keep observer mode read-only.

Out of scope for that foundation:

- OpenCV processing.
- YOLO/object detection.
- Browser camera access.
- Phone camera streaming.
- Automatic hit/miss scoring.
- Artifact storage.

## Owner Workflow Backlog

### Owner Settings

Move fixed defaults into owner-editable settings.

Candidate settings:

- Default club.
- Default distance.
- Default bucket size.
- Preferred Target Completion variant.

### Correction Tools

Keep logging low-friction, but add safe correction paths for mistakes.

Potential tools:

- Edit session notes/defaults.
- Edit or delete a mistaken bucket.
- Correct a Target Completion event.
- Preserve enough audit/provenance context to avoid confusing historical stats.

## Quality And UX Backlog

### Visual QA

The dashboard now depends on custom visuals, especially the target net map.

Future checks:

- Inspect desktop and mobile layouts after each major visual pass.
- Verify the net map remains readable with no data, sparse data, and real multi-run data.
- Verify target labels do not overlap on narrow screens.
- Keep empty states useful without making the dashboard feel unfinished.

### Accessibility And Interaction Polish

Keep the app usable beyond the happy path.

Potential improvements:

- Better keyboard focus states.
- Clearer button disabled states in Me Mode.
- Stronger ARIA labels for interactive visual controls.
- Touch-friendly target/game controls during active practice.

## Operations Backlog

### Backup And Restore Rehearsal

This should happen before the data becomes valuable enough that loss would hurt.

Goal:

- Prove that production data can be backed up and restored into a disposable database.

Deliverables:

- A documented backup command.
- A documented restore command.
- A tested rehearsal using non-production/disposable restore target.

### Deployment Hygiene

Current deployment is good enough and matches the BID-style NAS flow.

Future improvements:

- Document the exact `git push` then `./deploy.sh` flow.
- Add a short post-deploy smoke checklist.
- Consider an owner-visible build health/debug view if deployment issues become common.

## Not Planned For Now

- Google Forms or Google Sheets import.
- Public write access.
- Observer login.
- Automatic computer vision scoring.
- Complex multi-user support.
- Payment, accounts, or social features.

## Suggested Next Milestones

1. Record a few real Target Completion runs.
2. Reuse the net map in Me Mode and session detail.
3. Polish session detail with real data.
4. Add target trend mode.
5. Rehearse backup and restore.
6. Add owner settings.
7. Schedule CV foundation when the manual workflow and analytics feel stable.
