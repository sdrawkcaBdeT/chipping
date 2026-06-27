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

function OwnerSession() {
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [activeSession, setActiveSession] = useState(null);
  const [sessions, setSessions] = useState([]);

  async function refreshSessions() {
    const [active, history] = await Promise.all([
      api("/api/sessions/active"),
      api("/api/sessions")
    ]);
    setActiveSession(active);
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

  const activeFromEarlier = isEarlierDate(activeSession?.started_at);

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

      {error ? <p className="pageError">{error}</p> : null}
    </main>
  );
}

export default function App() {
  if (window.location.pathname === "/me/login") {
    return <MeLogin />;
  }

  if (window.location.pathname === "/me" || window.location.pathname === "/me/session/active") {
    return <OwnerSession />;
  }

  return <ObserverPlaceholder />;
}
