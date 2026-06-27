# Chip Tracker V0 — Final Spec Amendments

Apply these amendments to the main Chip Tracker V0 spec.

## Repository

Use the existing repository:

`sdrawkcaBdeT/chipping`

Production hostname:

`chip.cashbaggins.dev`

Do not create a new repo.

---

## Default site behavior

The default site state is **Observer Mode**.

When a visitor opens `chip.cashbaggins.dev`, they should land on the public/observer dashboard by default.

Observer Mode is read-only.

Observer Mode should not require login for V0 unless the user later chooses to add an observer password.

The observer can view:

* Overview dashboard
* Volume stats
* Session history
* Target map
* Target Completion stats
* Accuracy summaries

The observer cannot:

* Start sessions
* Stop sessions
* Log balls
* Edit data
* Delete data
* Export owner data
* Access LLM prompt helper
* Access settings

---

## Me Mode

Owner logging mode is entered from Observer Mode.

UI requirement:

There should be a clear but not obnoxious button, such as:

* `Me Mode`
* `Owner Login`
* `Log Practice`

When clicked, the user enters a PIN or password.

Successful owner login unlocks Me Mode.

V0 auth recommendation:

* Use a simple owner PIN/password stored in environment variables.
* Do not hardcode the PIN/password.
* Use HTTP-only signed cookie or JWT cookie after successful login.
* Backend must enforce owner-only write permissions.
* Frontend hiding owner controls is not sufficient by itself.

Suggested env vars:

* `OWNER_PIN` or `OWNER_PASSWORD`
* `JWT_SECRET`
* `SESSION_DAYS`
* `COOKIE_SECURE=true`

Observer Mode does not need a password in V0.

---

## Manual sessions

Sessions must be manually started and stopped.

Do not auto-create full practice sessions silently except for very explicit Quick Log behavior.

The user may have multiple discrete sessions in a single day.

Examples:

* Morning practice session: 8:10 AM to 8:29 AM
* Evening practice session: 6:45 PM to 7:12 PM

These should appear as separate sessions, not one combined day record.

---

## Session model

A session represents one intentional practice block.

Required fields:

* `id`
* `started_at`
* `ended_at`
* `status`: `active`, `completed`, `abandoned`
* `default_club`
* `default_distance_ft`
* `notes`
* `created_at`
* `updated_at`

Rules:

* A session starts only when the owner presses `Start Session`.
* A session ends only when the owner presses `Stop Session` / `End Session`, or manually marks it abandoned.
* Multiple sessions can exist on the same calendar date.
* The app should allow only one active session at a time by default.
* If an active session already exists, Me Mode should show `Continue Active Session` and `End Session`.
* If a session was left active from earlier, show a gentle warning:

  * “You have an active session from earlier. Continue it or end it?”

Do not silently merge sessions by day.

---

## Quick Log behavior update

Quick Log still must exist and must remain extremely simple.

However, because sessions are manual, Quick Log should behave like this:

### If there is an active session

Quick Log adds a quick-log game/bucket/partial bucket to the active session.

### If there is no active session

Show two options:

1. `Start session and log`
2. `Log as standalone quick session`

Recommended default:

`Start session and log`

For `Log as standalone quick session`, the app can create a very short completed session automatically with:

* `started_at = now`
* one quick log entry
* `ended_at = now`

This preserves the old “balls hit?” form behavior without corrupting the manual-session model.

Quick Log buttons:

* `+42 balls`
* `+21 balls`
* `+10 balls`
* `Custom`

Defaults:

* Club: 56°
* Distance: 15 ft

---

## Buckets and partial buckets

The app should use the word “bucket” because that matches the physical workflow, but the data model must support any ball count.

Default bucket size:

* 42 balls

Valid logged ball counts:

* 1 through any reasonable integer
* 42 is normal but not required

Examples:

* Full bucket: 42
* Half bucket: 21
* Warmup partial: 12
* Interrupted set: 31
* Custom: user entered

A game run can span multiple buckets or partial buckets.

A bucket/partial bucket belongs to:

* a session
* optionally a game run

---

## Remove old import requirement

Do not implement Google Forms / Google Sheets import in V0.

Remove the old import script requirement from the MVP/V0 scope.

Data export remains required.

---

## Flagship structured game: Target Completion

Target Completion should be treated as the main structured game in V0.

This is based on the user’s known successful tracking workflow.

Goal:

> Record how many balls it takes to hit each target. Once each target is hit, the game is done.

Primary variants:

1. Sequential 1-9
2. Random order 1-9

For each target:

* User attempts the current target until it is hit.
* User records misses and then hit.
* App records balls-to-hit for that target.
* Once hit, move to next target.
* Game completes when all 9 targets have been hit.

The app must support Target Completion spanning multiple buckets.

During Target Completion, show:

* Current target
* Current target attempts
* Completed targets
* Balls used in current bucket
* Total balls used in game
* Session timer
* Game timer

Buttons:

* `Miss / +1`
* `Hit Target`
* `Undo`
* `End Bucket / Retrieve`
* `Stop Game`
* `Stop Session`

When `End Bucket / Retrieve` is pressed:

* Close the current bucket/partial bucket.
* Preserve the active game run.
* Allow the user to start the next bucket and continue the same target/game.

Stats for Target Completion:

* Total balls to complete all 9
* Balls-to-hit by target
* Best completion score
* Median completion score
* Completion score trend over time
* Average balls-to-hit by target
* Sequential vs random comparison
* Completion time

---

## Revised route structure

Suggested frontend routes:

Observer default:

* `/`
* `/overview`
* `/volume`
* `/accuracy`
* `/targets`
* `/completion`
* `/sessions`

Owner / Me Mode:

* `/me/login`
* `/me`
* `/me/session/active`
* `/me/session/:id`
* `/me/quick-log`
* `/me/completion/new`
* `/me/game/:id`
* `/me/history`
* `/me/export`
* `/me/prompts`
* `/me/settings`

The app may use client routing, but direct refresh on these routes should work.

---

## Revised API behavior

### Public / observer endpoints

No login required:

* `GET /api/public/overview`
* `GET /api/public/volume`
* `GET /api/public/accuracy`
* `GET /api/public/targets`
* `GET /api/public/completion`
* `GET /api/public/sessions`

These must be read-only.

### Owner auth

* `POST /api/auth/owner-login`
* `POST /api/auth/logout`
* `GET /api/me`

`GET /api/me` should return:

* `{ mode: "observer" }` by default
* `{ mode: "owner" }` after owner login

### Owner session controls

* `POST /api/sessions/start`
* `POST /api/sessions/{id}/stop`
* `POST /api/sessions/{id}/abandon`
* `GET /api/sessions/active`
* `GET /api/sessions`
* `GET /api/sessions/{id}`
* `PATCH /api/sessions/{id}`
* `DELETE /api/sessions/{id}`

### Owner logging controls

* `POST /api/quick-log`
* `POST /api/game-runs`
* `POST /api/game-runs/{id}/stop`
* `POST /api/game-runs/{id}/buckets`
* `POST /api/game-runs/{id}/target-completion/miss`
* `POST /api/game-runs/{id}/target-completion/hit`
* `POST /api/game-runs/{id}/undo`
* `POST /api/buckets/{id}/end`

Codex can simplify endpoint naming if it keeps the behavior clean.

---

## Updated acceptance criteria

V0 is complete when:

1. Visiting `chip.cashbaggins.dev` shows Observer Mode by default.
2. Observer Mode is read-only.
3. Owner can enter Me Mode using a PIN/password.
4. Backend rejects all write actions unless owner-authenticated.
5. Owner can manually start a session.
6. Owner can manually stop a session.
7. Owner can create multiple distinct sessions on the same day.
8. Owner can quick-log `+42`, `+21`, `+10`, or custom balls.
9. Quick Log works inside an active session.
10. Quick Log has a sane standalone behavior when no session is active.
11. Owner can start Target Completion Sequential 1-9.
12. Target Completion records balls-to-hit per target.
13. Target Completion can span multiple buckets/retrievals.
14. Owner can end a bucket without ending the game.
15. Owner can stop a game without stopping the session.
16. Owner can stop the session from the active practice screen.
17. Observer can view Target Completion stats.
18. Owner can export CSV and JSON.
19. Old Google Forms import is not required.
20. App runs in Docker Compose with Postgres and is deployable to the UGREEN NAS / Cloudflare Tunnel pattern.

---

## Priority order

Build in this order:

1. FastAPI / React / Postgres / Docker skeleton.
2. Observer default dashboard shell.
3. Owner PIN/password auth.
4. Manual session start/stop.
5. Quick Log.
6. Buckets and partial buckets.
7. Target Completion Sequential 1-9.
8. Target Completion random order.
9. Basic public stats.
10. Export.
11. Prompt helper.
12. Other games and polish.

The core V0 test:

> Can the user press Start Session, practice, log without friction, then press Stop Session?

The second core V0 test:

> Can a visitor open the site and understand the user’s practice stats without being able to change anything?
