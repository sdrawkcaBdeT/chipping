# Chipping App: Camera Capture, CV Worker, and Project Provenance Context

## Purpose of this document

This document captures the planned future direction for the chipping tracker after the initial app is working.

The app is currently a personal indoor golf chipping tracker at:

`chip.cashbaggins.dev`

The user wants to expand it into a computer-vision-assisted practice tracker and also make the project more portfolio-visible over time.

This is not all meant to be implemented immediately. Treat this as design context plus a roadmap.

---

## Current physical practice setup

The user practices indoor chipping into a numbered chipping net.

Known setup:

* Chipping net with numbered targets 1 through 9.
* Default club: 56° wedge.
* Default distance: 15 feet from the bottom of the net.
* Floor is marked in 5-foot increments.
* User has 42 golf balls, usually hit as one physical “bucket” before retrieving balls.
* Buckets may be full or partial.
* Target Completion is the flagship game:

  * The app gives/uses a target order.
  * User hits until they make the current target.
  * Record balls-to-hit for each target.
  * Game ends once all targets have been hit.
  * The game may span multiple buckets.

---

## Available hardware for camera/CV

The user has multiple cameras in the room:

1. **Elgato webcam**, likely Elgato Facecam MK.2
   Good candidate for:

   * strike zone / mat camera
   * shot detection
   * club motion detection
   * ball disappearance from hitting area

2. **Laptop webcam**
   Good candidate for:

   * optional mechanics/body camera later
   * posture/pose experiments
   * secondary debug angle

3. **Samsung S25 Ultra**
   Good candidate for:

   * net/target camera
   * high-quality video
   * target-hole detection
   * closer framing of the net

4. **Laptop with strong GPU**
   Important architectural point:

   * The laptop can run local CV/ML inference.
   * The NAS should remain the app/database host.
   * The laptop should act as a CV worker that sends events to the app.

5. **UGREEN NAS**

   * Hosts the app/site/database.
   * Should not run heavy CV workloads unless there is a very good reason.

---

## Preferred architecture

Do not stream raw video to the NAS as the first approach.

Preferred architecture:

```text
Camera(s)
  ↓
Laptop CV Worker with GPU
  ↓
Small JSON events
  ↓
chip.cashbaggins.dev API on NAS
  ↓
Active session/game updates
```

The app should remain the tracker, database, and UI.

The laptop should be the CV brain.

The app receives small events such as:

```json
{
  "eventType": "shot_detected",
  "targetNumber": 4,
  "result": "likely_miss",
  "confidence": 0.71,
  "source": "laptop-cv-worker"
}
```

or:

```json
{
  "eventType": "target_hit",
  "targetNumber": 4,
  "result": "likely_hit",
  "confidence": 0.88,
  "source": "phone-net-camera"
}
```

The app should initially display these as suggested events requiring confirmation, not silently auto-score everything.

---

## Camera role plan

Do not try to make one camera do everything.

### Elgato webcam: shot/attempt detector

Suggested placement:

* Behind or near the hitting area.
* It should see the mat, ball, and club.

Primary job:

> Did a shot happen?

Potential signals:

* Club motion through ball zone.
* Ball disappears from original position.
* Motion spike near mat.
* Optional audio spike.

Expected reliability: high.

### S25 Ultra: net/target detector

Suggested placement:

* Pointed at the chipping net.
* Net should fill as much of the frame as practical.
* Ideally stable on a tripod/chair.
* Good lighting on the net.

Primary job:

> Did the active target get hit?

Important simplification:

The app usually knows the current target during Target Completion. Therefore the CV system does not need to classify all 9 targets every time. It mainly needs to answer:

> Current target is 4. Did target 4 get hit after this shot?

This is easier than full multi-class target classification.

### Laptop webcam: mechanics/debug camera

Defer this from scoring V1.

Possible future uses:

* Body pose estimation.
* Swing mechanics.
* Head movement.
* Setup consistency.
* Tempo.
* Debug/reference angle.

---

## Technology options discussed

### Start with classical OpenCV

This should be the first serious attempt.

Reason:

* Camera is fixed.
* Net is fixed.
* Targets are fixed.
* Lighting can be controlled.
* We can define regions of interest manually.

Useful techniques:

* Frame differencing.
* Background subtraction.
* Fixed region-of-interest scoring.
* White-pixel / brightness-change detection.
* Motion spike detection.
* Contour detection.
* Optional HSV thresholds for colored target rings.
* Calibration UI to draw boxes around targets.

For the first version, avoid “track the whole ball flight.” Instead use event detection:

1. Shot happened.
2. Open short detection window.
3. Watch active target zone.
4. If active target zone spikes, likely hit.
5. If no spike, likely miss.

### ML/object detection later

Possible future models:

* YOLO-style detector for ball/club/net/target regions.
* Segmentation model for target/net movement.
* Small classifier trained on short post-shot clips.
* Pose estimation for mechanics.

But do not start with full ML unless classical CV fails.

This setup may work better with boring ROI-based CV than generic object detection because the scene is fixed and constrained.

### Browser-based CV option

It is possible for the website to access a camera through browser camera APIs and process frames locally in the browser.

Possible stack:

* Browser `getUserMedia`.
* Canvas frame processing.
* OpenCV.js or custom JavaScript frame-diff logic.
* MediaPipe tasks for pose/object detection.
* ONNX Runtime Web / WebGPU for client-side models.

This is attractive for a `/me/cv-lab` page, especially for calibration/debugging.

However, for the main reliable version, a local Python CV worker on the GPU laptop may be simpler and more powerful.

### Server-side video processing

It is technically possible to stream video to the site and process it server-side.

Possible approaches:

* WebRTC to server.
* WebSocket JPEG/video frames.
* RTSP/IP camera feed.
* MediaRecorder chunks.
* Upload short clips for offline processing.

But this is not preferred for V1 because:

* Video streaming through Cloudflare/NAS adds complexity.
* NAS likely should not do heavy inference.
* Latency and bandwidth become unnecessary problems.
* The laptop has the GPU and is in the room.

Preferred V1:

> Local inference on laptop, tiny event POSTs to the app.

---

## CV integration in the app

The app should eventually have a CV integration layer but should not process video in the main app container.

### Proposed backend additions

Add a `cv_events` table.

Suggested fields:

```text
cv_events
- id
- session_id
- game_run_id
- event_type
- target_number
- result
- confidence
- source
- payload_json
- created_at
```

Possible `event_type` values:

```text
shot_detected
target_hit
target_miss
likely_hit
likely_miss
wrong_target
unclear
worker_heartbeat
calibration_update
```

Possible `result` values:

```text
make
miss
near
likely_make
likely_miss
unknown
```

### Proposed endpoints

Owner/CV-worker only:

```text
GET  /api/cv/active-context
POST /api/cv/events
GET  /api/cv/events/recent
```

Suggested `GET /api/cv/active-context` response:

```json
{
  "sessionId": 12,
  "gameRunId": 44,
  "gameType": "target_completion_sequential",
  "activeTarget": 5,
  "currentBucketBallCount": 17,
  "distanceFt": 15,
  "club": "56°"
}
```

Suggested `POST /api/cv/events` request:

```json
{
  "eventType": "shot_detected",
  "targetNumber": 5,
  "result": "likely_hit",
  "confidence": 0.86,
  "source": "laptop-yolo-worker",
  "payload": {
    "camera": "s25-net",
    "modelVersion": "none-opencv-roi-v0",
    "roiMotionScore": 0.92
  }
}
```

### Security

Use a shared CV worker API key.

Suggested env var:

```text
CV_WORKER_API_KEY
```

The CV worker should authenticate by header, for example:

```text
Authorization: Bearer <CV_WORKER_API_KEY>
```

or:

```text
X-CV-Worker-Key: <CV_WORKER_API_KEY>
```

Backend must not allow public users to post CV events.

### Frontend page

Add an owner-only page:

```text
/me/cv
```

or:

```text
/me/cv-lab
```

It should show:

* Active session/game context.
* Current target.
* Recent CV events.
* Worker connected/disconnected status.
* Last event confidence.
* Pending suggested result.
* Confirm/reject/undo controls.
* Later: calibration preview/debug overlay.

Do not auto-score in first integration milestone. Just record and display events.

---

## Intended Target Completion CV flow

Manual Target Completion already works or should work first.

CV-assisted flow:

1. User starts Target Completion.
2. App knows current target.
3. CV worker polls `/api/cv/active-context`.
4. Elgato/mat camera detects a shot.
5. Worker opens a short detection window.
6. Phone/net camera watches the active target ROI.
7. Worker posts likely result to app.
8. App shows pending suggestion:

   * Confirm Hit
   * Confirm Miss
   * Actually Hit
   * Actually Miss
   * Undo
9. Once reliable, add optional auto-confirm above a confidence threshold.

Example:

```text
Current target: 4

CV event:
Shot detected.
Target 4 region spiked.
Likely hit, confidence 0.84.

UI:
[Confirm Hit] [Actually Miss] [Undo]
```

Eventually:

```text
If confidence >= threshold:
  auto-advance to next target
  show Undo button
```

---

## Local CV worker concept

Create a separate local worker project or repo directory later.

Possible names:

```text
cv_worker/
chipping_cv_worker/
tools/cv_worker/
```

It may be better as a separate small Python package, but it can initially live in the same repo if convenient.

Responsibilities:

* Connect to cameras.
* Run calibration.
* Detect shot events.
* Detect target events.
* Save optional debug clips/artifacts.
* POST events to the chipping app.
* Poll active context from the app.
* Print useful local logs.

Possible stack:

```text
Python
OpenCV
NumPy
requests/httpx
optional Ultralytics YOLO
optional MediaPipe
optional PyTorch
```

Initial worker should be boring OpenCV only.

---

## Feasibility experiment

Before fully integrating, record test footage.

Recommended experiment:

1. Put Elgato on mat/strike zone.
2. Put S25 pointed at net.
3. Record 20-50 chips.
4. Include makes and misses.
5. Call the target number out loud before each shot.
6. Test different settings:

   * 1080p/60
   * 4K/60
   * 720p/120 or 4K/120 if available
7. Inspect whether:

   * shot events are visible
   * net target motion is visible
   * ball flash is visible
   * active target hits are distinguishable from misses
   * lighting creates false positives

Use the recordings to decide whether OpenCV ROI is enough.

---

# Portfolio / Resume Visibility Direction

## Core idea

The chipping tracker should become more than a private tool. It should become a visible personal analytics/computer-vision project.

Goal framing:

> A self-hosted, computer-vision-assisted sports analytics platform with versioned data capture, model artifacts, session replay, public dashboards, and project provenance.

The app should show not only golf practice data, but also the evolution of the system over time.

---

## Session provenance

Every session should know what version of the system recorded it.

On session start, snapshot relevant build/version fields.

Suggested session provenance fields:

```text
app_git_sha
frontend_git_sha
backend_git_sha
schema_version
build_version
cv_worker_git_sha
cv_worker_version
cv_model_version
calibration_id
camera_config_id
```

Initial minimal version:

```text
app_git_sha
build_version
schema_version
```

The session detail page should show:

```text
Recorded with:
App commit: abc1234
Schema version: 2026_06_27_001
CV worker: none
Model: none
Calibration: none
```

### GitHub link at time of session

Each session should eventually link to the GitHub repo at the commit that was live when the session was recorded.

Example link pattern:

```text
https://github.com/sdrawkcaBdeT/chipping/tree/<app_git_sha>
```

Label:

```text
View code at time of session
```

This does not literally run the old app, but it proves what code existed.

---

## “Time-warp” concept

The user likes the idea of clicking on a session and “time-warping” the website to that point in time.

There are levels:

### Level 1: GitHub commit link

Easy and high value.

Store app git SHA and link to repo tree at that commit.

### Level 2: Session screenshots / UI snapshots

Store images showing what the app/session page/dashboard looked like then.

This is probably more stable and useful than running old builds.

Possible artifacts:

* session page screenshot
* dashboard screenshot
* CV debug overlay screenshot
* target map screenshot
* chart screenshot

### Level 3: Replay artifacts

For CV sessions, store:

* raw video clip
* annotated video
* detection event JSON
* model output JSON
* calibration file
* camera config
* confidence timeline
* false positive/false negative notes

### Level 4: Actual old app builds

Possible but defer.

Could tag Docker images by git SHA and later spin up old builds.

This is probably overkill for now.

Do not implement Level 4 until there is a strong reason.

---

## Session artifacts

Add a future `session_artifacts` table.

Suggested fields:

```text
session_artifacts
- id
- session_id
- artifact_type
- title
- description
- storage_uri
- sha256_hash
- size_bytes
- mime_type
- visibility
- app_git_sha
- cv_worker_git_sha
- model_version
- created_at
```

Possible `artifact_type` values:

```text
raw_video
annotated_video
cv_debug_json
session_export_json
screenshot
model_output
calibration
camera_config
chart_image
writeup
```

Possible `visibility` values:

```text
private
public
unlisted
```

Important:

Do not commit raw videos to GitHub. Store large artifacts in NAS storage, object storage, Cloudflare R2, S3-compatible storage, or similar.

GitHub should store:

* code
* docs
* curated small samples
* links/manifests

Large session videos should live outside the repo.

---

## Public project timeline

Add a public page eventually:

```text
/build
```

or:

```text
/project
```

Purpose:

Show the evolution of the app as a portfolio.

Milestone examples:

```text
V0 — Manual Tracker
- Manual sessions
- Quick Log
- Target Completion
- Public observer dashboard

V1 — CV Event Ingestion
- Local CV worker posts shot events
- Owner confirms/rejects detections

V2 — Net Target Detection
- Phone camera watches target ROIs
- Annotated video artifacts
- Target Completion assistance

V3 — Model-Assisted Scoring
- Trained detector/classifier
- Session replay
- Confidence timeline

V4 — Mechanics/Pose Analysis
- Swing/body mechanics experiments
- Pose landmark artifacts
```

Each milestone can link to:

* GitHub commit/PR
* demo session
* screenshots
* artifacts
* writeup

This helps make the project resume-visible.

---

## Resume-friendly framing

Possible framing of the project:

> Built a self-hosted sports analytics platform for indoor golf chipping practice, combining FastAPI, React, Postgres, Docker, Cloudflare Tunnel, computer vision event ingestion, versioned session provenance, public dashboards, and model/session artifact tracking.

Potential eventual bullet:

> Designed and deployed a computer-vision-assisted golf practice tracker that uses multi-camera local inference to detect shots and target hits, records structured practice sessions, stores model/session artifacts, and exposes public analytics dashboards for longitudinal performance tracking.

---

# Open decisions

The following decisions are intentionally not finalized.

## CV architecture decisions

1. Should the CV worker live inside the main repo or a separate repo?

   * Default recommendation: start inside `tools/cv_worker/` or `cv_worker/` for speed.
   * Split later if it grows.

2. Should the app include browser-based `/me/cv-lab` first, or start with a Python laptop worker?

   * Default recommendation: start with app CV event endpoints, then Python worker.
   * Browser CV lab can be added for calibration/debugging.

3. How should phone video reach the laptop worker?

   * Options:

     * Use the phone as an IP/webcam.
     * Use a phone webcam app.
     * Record offline clips first.
     * Build Android app later.
   * Default: record offline clips first, then live phone-as-camera.

4. Should CV events auto-score immediately?

   * Default: no.
   * First version should show suggestions and require confirmation.
   * Auto-confirm only after enough confidence.

5. Should the model detect all targets or only the active target?

   * Default: only active target at first.
   * App knows active target, so the problem is easier.

6. Should we train a model right away?

   * Default: no.
   * Start with OpenCV ROI detection.
   * Save data/artifacts for future training.

7. Should body mechanics / pose be included in scoring?

   * Default: no.
   * Treat mechanics as a later experimental feature.

## Artifact/provenance decisions

1. Where should large artifacts be stored?

   * Options:

     * NAS file storage
     * Cloudflare R2
     * S3-compatible object storage
     * GitHub Releases for curated demos only
   * Default: NAS storage initially, but design `storage_uri` abstractly.

2. Should public observers see artifacts?

   * Default: only artifacts marked `public`.

3. Should every session generate artifacts automatically?

   * Default: no.
   * Start with manual artifact attachment and Git SHA provenance.
   * CV worker can later auto-create artifacts.

4. Should old app builds be runnable?

   * Default: no.
   * Use GitHub commit links and screenshots first.

5. Should the project timeline be public?

   * Default: yes, eventually.
   * It is separate from the practice dashboard.

---

# Recommended implementation order

Do not implement all of this at once.

Suggested order:

## Milestone A: Build provenance

Add build/session provenance.

* Add app/build git SHA.
* Store app git SHA on session start.
* Show “View code at time of session” on session detail.
* Add build version to app footer/about page.

## Milestone B: CV event ingestion

Add the app-side hooks only.

* Add `cv_events` table.
* Add CV worker API key.
* Add `/api/cv/active-context`.
* Add `/api/cv/events`.
* Add `/api/cv/events/recent`.
* Add owner-only `/me/cv` debug page.
* Do not auto-score yet.

## Milestone C: Local CV worker proof of concept

Create a local Python worker.

* Connect to one camera.
* Detect shot events using OpenCV.
* POST `shot_detected` events to the app.
* Display/log debug output locally.

## Milestone D: Net target detection

Use phone/net camera.

* Manual ROI calibration for targets 1-9.
* Detect motion/white flash in active target region.
* POST likely hit/miss events.
* App shows confirmation UI.

## Milestone E: Artifact tracking

Add session artifacts.

* Add `session_artifacts` table.
* Add owner UI to attach artifacts.
* Add public/private visibility.
* Add artifact list to session detail page.

## Milestone F: Project timeline

Add public `/build` or `/project` page.

* Show milestones.
* Link to demo sessions.
* Link to GitHub commits.
* Link to screenshots/artifacts.

## Milestone G: ML/model-assisted detection

Only after collecting data.

* Save labeled clips/events.
* Train or fine-tune a detector/classifier.
* Store model version.
* Record model outputs as artifacts.

---

# Next Codex task recommendation

The next coding task should likely be one of these:

## Option 1: Add build provenance first

Best if we want to make every future session portfolio-aware.

Scope:

* Add build/git SHA support.
* Store SHA on sessions.
* Show GitHub commit link on session detail.

## Option 2: Add CV event ingestion first

Best if we want to prepare for camera experiments.

Scope:

* Add `cv_events` table.
* Add worker API key.
* Add `/api/cv/active-context`.
* Add `/api/cv/events`.
* Add `/me/cv` debug page.

## Option 3: Add both lightweight foundations

Reasonable if current app is simple and stable.

Scope:

* Add session provenance fields.
* Add `cv_events` table.
* Add basic CV debug endpoints/page.
* Do not implement actual computer vision yet.

Recommended: Option 3 if app code is currently clean. Otherwise Option 1 first.
