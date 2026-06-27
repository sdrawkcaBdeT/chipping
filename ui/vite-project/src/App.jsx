import { useEffect, useState } from "react";

import "./styles.css";

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    throw new Error(data?.detail || "Request failed");
  }

  return data;
}

function formatDateTime(value) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

function sessionDuration(session) {
  if (!session) {
    return "";
  }

  const start = new Date(session.started_at).getTime();
  const end = session.ended_at ? new Date(session.ended_at).getTime() : Date.now();
  const minutes = Math.max(0, Math.round((end - start) / 60000));

  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

function isEarlierDate(value) {
  if (!value) {
    return false;
  }

  return new Date(value).toDateString() !== new Date().toDateString();
}

const QUICK_LOG_COUNTS = [42, 21, 10];

function ObserverPlaceholder() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Observer Mode</p>
          <h1>Chip Tracker</h1>
        </div>
        <a className="primaryAction" href="/me/login">
          Log Practice
        </a>
      </header>

      <section className="panel">
        <div className="panelText">
          <p className="eyebrow">Read-only dashboard</p>
          <h2>Practice summary coming online.</h2>
          <p>
            Public chipping stats will land here as sessions, logs, and target games are
            added.
          </p>
        </div>
        <div className="targetPreview" aria-hidden="true">
          <span className="target targetOne" />
          <span className="target targetTwo" />
          <span className="target targetThree" />
          <span className="target targetFour" />
          <span className="target targetFive" />
        </div>
      </section>
    </main>
  );
}

function MeLogin() {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      await api("/api/auth/owner-login", {
        method: "POST",
        body: JSON.stringify({ pin })
      });
      window.location.href = "/me";
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell compact">
      <header className="topbar">
        <div>
          <p className="eyebrow">Me Mode</p>
          <h1>Log Practice</h1>
        </div>
        <a className="secondaryAction" href="/">
          Observer
        </a>
      </header>

      <section className="panel loginPanel">
        <div className="panelText">
          <p className="eyebrow">Owner login</p>
          <h2>Enter Me Mode.</h2>
          <p>Owner controls unlock after PIN verification.</p>
        </div>
        <form className="loginForm" onSubmit={handleSubmit}>
          <label htmlFor="pin">PIN</label>
          <input
            id="pin"
            name="pin"
            type="password"
            autoComplete="current-password"
            value={pin}
            onChange={(event) => setPin(event.target.value)}
          />
          {error ? <p className="formError">{error}</p> : null}
          <button type="submit" disabled={busy || !pin}>
            {busy ? "Checking..." : "Enter Me Mode"}
          </button>
        </form>
      </section>
    </main>
  );
}

function SessionStatusPill({ status }) {
  return <span className={`statusPill ${status}`}>{status}</span>;
}

function QuickLogPanel({ activeSession, buckets, disabled, onQuickLog }) {
  const [selectedCount, setSelectedCount] = useState(42);
  const [customCount, setCustomCount] = useState("");
  const [useCustom, setUseCustom] = useState(false);

  const customBallCount = Number(customCount);
  const selectedBallCount = useCustom ? customBallCount : selectedCount;
  const canLog =
    Number.isInteger(selectedBallCount) && selectedBallCount >= 1 && selectedBallCount <= 500;
  const recentBuckets = buckets.filter((bucket) => bucket.ball_count > 0).slice(0, 4);

  function pickCount(count) {
    setSelectedCount(count);
    setUseCustom(false);
  }

  async function logCustom(mode) {
    if (!canLog) {
      return;
    }

    await onQuickLog(selectedBallCount, mode);
    if (useCustom) {
      setCustomCount("");
    }
  }

  return (
    <div className="quickLogPanel">
      <div className="historyHeader">
        <p className="eyebrow">Quick Log</p>
      </div>

      {activeSession ? (
        <div className="quickLogActive">
          <div className="quickButtons">
            {QUICK_LOG_COUNTS.map((count) => (
              <button
                type="button"
                key={count}
                onClick={() => onQuickLog(count, "active")}
                disabled={disabled}
              >
                +{count}
              </button>
            ))}
          </div>
          <div className="customLogRow">
            <input
              aria-label="Custom ball count"
              inputMode="numeric"
              min="1"
              max="500"
              type="number"
              value={customCount}
              onChange={(event) => {
                setCustomCount(event.target.value);
                setUseCustom(true);
              }}
              placeholder="Custom"
            />
            <button
              className="secondaryButton"
              type="button"
              onClick={() => logCustom("active")}
              disabled={disabled || !canLog || !useCustom}
            >
              Log
            </button>
          </div>
        </div>
      ) : (
        <div className="quickLogStandalone">
          <div className="countPicker" role="group" aria-label="Quick log amount">
            {QUICK_LOG_COUNTS.map((count) => (
              <button
                className={!useCustom && selectedCount === count ? "selected" : ""}
                type="button"
                key={count}
                onClick={() => pickCount(count)}
                disabled={disabled}
              >
                +{count}
              </button>
            ))}
          </div>
          <input
            aria-label="Custom ball count"
            inputMode="numeric"
            min="1"
            max="500"
            type="number"
            value={customCount}
            onChange={(event) => {
              setCustomCount(event.target.value);
              setUseCustom(true);
            }}
            placeholder="Custom"
          />
          <div className="quickChoiceGrid">
            <button
              type="button"
              onClick={() => logCustom("start_session")}
              disabled={disabled || !canLog}
            >
              Start Session and Log
            </button>
            <button
              className="secondaryButton"
              type="button"
              onClick={() => logCustom("standalone")}
              disabled={disabled || !canLog}
            >
              Log Standalone
            </button>
          </div>
        </div>
      )}

      {activeSession ? (
        <div className="bucketListWrap">
          <p className="eyebrow">Active session logs</p>
          {recentBuckets.length ? (
            <ol className="bucketList">
              {recentBuckets.map((bucket) => (
                <li key={bucket.id}>
                  <strong>+{bucket.ball_count}</strong>
                  <span>
                    {bucket.club} / {bucket.distance_ft} ft
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="muted">No balls logged yet.</p>
          )}
        </div>
      ) : null}
    </div>
  );
}

function TargetCompletionPanel({
  activeSession,
  activeGame,
  disabled,
  onStartGame,
  onGameAction,
  onEndBucket
}) {
  if (!activeSession) {
    return null;
  }

  if (!activeGame) {
    return (
      <div className="targetGamePanel">
        <div>
          <p className="eyebrow">Target Completion</p>
          <h2>Start 1-9</h2>
        </div>
        <div className="gameStartGrid">
          <button type="button" onClick={() => onStartGame("sequential")} disabled={disabled}>
            Sequential 1-9
          </button>
          <button
            className="secondaryButton"
            type="button"
            onClick={() => onStartGame("random")}
            disabled={disabled}
          >
            Random 1-9
          </button>
        </div>
      </div>
    );
  }

  const currentTarget = activeGame.current_target;

  return (
    <div className="targetGamePanel activeTargetGame">
      <div className="gameHeader">
        <div>
          <p className="eyebrow">Target Completion</p>
          <h2>{currentTarget ? `Target ${currentTarget.target_number}` : "Complete"}</h2>
        </div>
        <SessionStatusPill status={activeGame.variant} />
      </div>

      <div className="gameStats">
        <div>
          <span>Target attempts</span>
          <strong>{currentTarget ? currentTarget.attempts : 0}</strong>
        </div>
        <div>
          <span>Bucket balls</span>
          <strong>{activeGame.current_bucket_balls}</strong>
        </div>
        <div>
          <span>Total balls</span>
          <strong>{activeGame.total_balls_used}</strong>
        </div>
        <div>
          <span>Game timer</span>
          <strong>{sessionDuration(activeGame)}</strong>
        </div>
      </div>

      <ol className="targetGrid" aria-label="Target order">
        {activeGame.targets.map((target) => (
          <li
            className={[
              target.hit ? "completed" : "",
              currentTarget?.target_number === target.target_number ? "current" : ""
            ]
              .filter(Boolean)
              .join(" ")}
            key={target.target_number}
          >
            <strong>{target.target_number}</strong>
            <span>{target.attempts}</span>
          </li>
        ))}
      </ol>

      <div className="gameActionGrid">
        <button
          type="button"
          onClick={() => onGameAction("miss")}
          disabled={disabled || !currentTarget || activeGame.status !== "active"}
        >
          Miss / +1
        </button>
        <button
          type="button"
          onClick={() => onGameAction("hit")}
          disabled={disabled || !currentTarget || activeGame.status !== "active"}
        >
          Hit Target
        </button>
        <button
          className="secondaryButton"
          type="button"
          onClick={() => onGameAction("undo")}
          disabled={disabled || activeGame.total_balls_used === 0}
        >
          Undo
        </button>
        <button
          className="secondaryButton"
          type="button"
          onClick={onEndBucket}
          disabled={disabled || !activeGame.active_bucket || activeGame.status !== "active"}
        >
          End Bucket / Retrieve
        </button>
        <button
          className="secondaryButton danger"
          type="button"
          onClick={() => onGameAction("stop")}
          disabled={disabled || activeGame.status !== "active"}
        >
          Stop Game
        </button>
      </div>
    </div>
  );
}

function OwnerSession() {
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [quickLogBusy, setQuickLogBusy] = useState(false);
  const [gameBusy, setGameBusy] = useState(false);
  const [error, setError] = useState("");
  const [quickLogMessage, setQuickLogMessage] = useState("");
  const [gameMessage, setGameMessage] = useState("");
  const [activeSession, setActiveSession] = useState(null);
  const [activeBuckets, setActiveBuckets] = useState([]);
  const [activeGame, setActiveGame] = useState(null);
  const [sessions, setSessions] = useState([]);

  async function refreshSessions() {
    const [active, history, game] = await Promise.all([
      api("/api/sessions/active"),
      api("/api/sessions"),
      api("/api/game-runs/active")
    ]);
    const buckets = active ? await api(`/api/sessions/${active.id}/buckets`) : [];

    setActiveSession(active);
    setActiveBuckets(buckets);
    setActiveGame(game);
    setSessions(history);
  }

  useEffect(() => {
    let ignore = false;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const me = await api("/api/me");
        if (me.mode !== "owner") {
          window.location.href = "/me/login";
          return;
        }

        await refreshSessions();
      } catch (error) {
        if (!ignore) {
          setError(error.message);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      ignore = true;
    };
  }, []);

  async function startSession() {
    setBusy(true);
    setError("");
    setQuickLogMessage("");
    setGameMessage("");

    try {
      const session = await api("/api/sessions/start", {
        method: "POST",
        body: JSON.stringify({
          default_club: "56",
          default_distance_ft: 15
        })
      });
      setActiveSession(session);
      await refreshSessions();
      window.history.replaceState({}, "", "/me/session/active");
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function stopSession() {
    if (!activeSession) {
      return;
    }

    setBusy(true);
    setError("");
    setQuickLogMessage("");
    setGameMessage("");

    try {
      await api(`/api/sessions/${activeSession.id}/stop`, { method: "POST" });
      await refreshSessions();
      window.history.replaceState({}, "", "/me");
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function abandonSession() {
    if (!activeSession) {
      return;
    }

    setBusy(true);
    setError("");
    setQuickLogMessage("");
    setGameMessage("");

    try {
      await api(`/api/sessions/${activeSession.id}/abandon`, { method: "POST" });
      await refreshSessions();
      window.history.replaceState({}, "", "/me");
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    window.location.href = "/";
  }

  async function quickLog(ballCount, mode) {
    setQuickLogBusy(true);
    setError("");
    setQuickLogMessage("");
    setGameMessage("");

    try {
      const result = await api("/api/quick-log", {
        method: "POST",
        body: JSON.stringify({
          ball_count: ballCount,
          mode
        })
      });
      await refreshSessions();
      if (result.session.status === "active") {
        window.history.replaceState({}, "", "/me/session/active");
      }
      setQuickLogMessage(`Logged +${result.bucket.ball_count}`);
    } catch (error) {
      setError(error.message);
    } finally {
      setQuickLogBusy(false);
    }
  }

  async function startTargetCompletion(variant) {
    setGameBusy(true);
    setError("");
    setGameMessage("");
    setQuickLogMessage("");

    try {
      const game = await api("/api/game-runs", {
        method: "POST",
        body: JSON.stringify({ variant })
      });
      setActiveGame(game);
      await refreshSessions();
      window.history.replaceState({}, "", `/me/game/${game.id}`);
    } catch (error) {
      setError(error.message);
    } finally {
      setGameBusy(false);
    }
  }

  async function gameAction(action) {
    if (!activeGame) {
      return;
    }

    const endpoints = {
      miss: `/api/game-runs/${activeGame.id}/target-completion/miss`,
      hit: `/api/game-runs/${activeGame.id}/target-completion/hit`,
      undo: `/api/game-runs/${activeGame.id}/undo`,
      stop: `/api/game-runs/${activeGame.id}/stop`
    };

    setGameBusy(true);
    setError("");
    setGameMessage("");
    setQuickLogMessage("");

    try {
      const game = await api(endpoints[action], { method: "POST" });
      setActiveGame(game.status === "active" ? game : null);
      await refreshSessions();
      if (game.status === "completed") {
        setActiveGame(game);
        setGameMessage(`Target Completion complete: ${game.total_balls_used} balls`);
        window.history.replaceState({}, "", "/me/session/active");
      } else if (game.status === "stopped") {
        setGameMessage("Target Completion stopped");
        window.history.replaceState({}, "", "/me/session/active");
      } else {
        window.history.replaceState({}, "", `/me/game/${game.id}`);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setGameBusy(false);
    }
  }

  async function endGameBucket() {
    if (!activeGame?.active_bucket) {
      return;
    }

    setGameBusy(true);
    setError("");
    setGameMessage("");
    setQuickLogMessage("");

    try {
      await api(`/api/buckets/${activeGame.active_bucket.id}/end`, { method: "POST" });
      const game = await api(`/api/game-runs/${activeGame.id}`);
      setActiveGame(game);
      await refreshSessions();
      setGameMessage("Bucket ended");
    } catch (error) {
      setError(error.message);
    } finally {
      setGameBusy(false);
    }
  }

  const activeFromEarlier = isEarlierDate(activeSession?.started_at);
  const activeBallTotal = activeBuckets.reduce((total, bucket) => total + bucket.ball_count, 0);
  const controlsDisabled = loading || busy || quickLogBusy || gameBusy;

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Me Mode</p>
          <h1>Practice Session</h1>
        </div>
        <div className="topbarActions">
          <a className="secondaryAction" href="/">
            Observer
          </a>
          <button className="secondaryButton" type="button" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      <section className="sessionGrid">
        <div className="panel sessionPanel">
          <div className="panelText">
            <p className="eyebrow">Session controls</p>
            <h2>{activeSession ? "Active session" : "Ready to start"}</h2>
            {activeFromEarlier ? (
              <p className="warningText">
                You have an active session from earlier. Continue it or end it?
              </p>
            ) : null}
            {activeSession ? (
              <div className="sessionFacts">
                <div>
                  <span>Started</span>
                  <strong>{formatDateTime(activeSession.started_at)}</strong>
                </div>
                <div>
                  <span>Duration</span>
                  <strong>{sessionDuration(activeSession)}</strong>
                </div>
                <div>
                  <span>Default</span>
                  <strong>
                    {activeSession.default_club} / {activeSession.default_distance_ft} ft
                  </strong>
                </div>
                <div>
                  <span>Balls logged</span>
                  <strong>{activeBallTotal}</strong>
                </div>
              </div>
            ) : (
              <p>Start a manual practice block before logging balls.</p>
            )}
          </div>

          <div className="controlStack">
            {activeSession ? (
              <>
                <a className="primaryAction wide" href="/me/session/active">
                  Continue Active Session
                </a>
                <button type="button" onClick={stopSession} disabled={busy}>
                  End Session
                </button>
                <button
                  className="secondaryButton danger"
                  type="button"
                  onClick={abandonSession}
                  disabled={busy}
                >
                  Abandon
                </button>
              </>
            ) : (
              <button type="button" onClick={startSession} disabled={busy || loading}>
                {busy ? "Starting..." : "Start Session"}
              </button>
            )}
          </div>
        </div>

        <TargetCompletionPanel
          activeSession={activeSession}
          activeGame={activeGame}
          disabled={controlsDisabled}
          onStartGame={startTargetCompletion}
          onGameAction={gameAction}
          onEndBucket={endGameBucket}
        />

        {!activeGame ? (
          <QuickLogPanel
            activeSession={activeSession}
            buckets={activeBuckets}
            disabled={controlsDisabled}
            onQuickLog={quickLog}
          />
        ) : null}

        <div className="historyPanel">
          <div className="historyHeader">
            <p className="eyebrow">Recent sessions</p>
          </div>
          {loading ? (
            <p className="muted">Loading...</p>
          ) : sessions.length ? (
            <ol className="sessionList">
              {sessions.slice(0, 5).map((session) => (
                <li key={session.id}>
                  <div>
                    <strong>{formatDateTime(session.started_at)}</strong>
                    <span>{sessionDuration(session)}</span>
                  </div>
                  <SessionStatusPill status={session.status} />
                </li>
              ))}
            </ol>
          ) : (
            <p className="muted">No sessions yet.</p>
          )}
        </div>
      </section>

      {quickLogMessage ? <p className="successMessage">{quickLogMessage}</p> : null}
      {gameMessage ? <p className="successMessage">{gameMessage}</p> : null}
      {error ? <p className="pageError">{error}</p> : null}
    </main>
  );
}

export default function App() {
  if (window.location.pathname === "/me/login") {
    return <MeLogin />;
  }

  if (
    window.location.pathname === "/me" ||
    window.location.pathname === "/me/session/active" ||
    window.location.pathname === "/me/completion/new" ||
    window.location.pathname.startsWith("/me/game/")
  ) {
    return <OwnerSession />;
  }

  return <ObserverPlaceholder />;
}
