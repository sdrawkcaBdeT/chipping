import { useEffect, useState } from "react";

import { APP_ERAS, codeUrlForSha, resolveAppEra } from "./data/appEras";
import chippingNetTargetsLayout from "./data/chippingNetTargetsLayout.json";
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

function formatDateOnly(value) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(value));
}

function formatNumber(value) {
  return new Intl.NumberFormat().format(value || 0);
}

function formatMaybeNumber(value) {
  if (value === null || value === undefined) {
    return "n/a";
  }

  return formatNumber(value);
}

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "n/a";
  }

  return `${Math.round(value * 100)}%`;
}

function formatDurationSeconds(value) {
  if (!value) {
    return "0 min";
  }

  const minutes = Math.max(0, Math.round(value / 60));
  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
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
const DASHBOARD_RANGES = [
  {
    key: "last_session",
    label: "Last session",
    heroSuffix: "in the last session"
  },
  {
    key: "7d",
    label: "7D",
    heroSuffix: "in the last 7 days"
  },
  {
    key: "30d",
    label: "30D",
    heroSuffix: "in the last 30 days"
  },
  {
    key: "all",
    label: "All",
    heroSuffix: "tracked"
  }
];
const TARGET_MAP_MODES = [
  { key: "performance", label: "Performance" },
  { key: "last_run", label: "Last Run" }
];
const NET_MESH_LINES = [16, 24, 32, 40, 48, 56, 64, 72, 80, 88];

function sourceLabel(source) {
  return source.replaceAll("_", " ");
}

function publicStatsPath(path, rangeKey) {
  const params = new URLSearchParams({ range: rangeKey });
  return `${path}?${params.toString()}`;
}

function rangeOption(rangeKey) {
  return DASHBOARD_RANGES.find((item) => item.key === rangeKey) || DASHBOARD_RANGES[2];
}

function scoreDeltaLabel(value) {
  if (value === null || value === undefined) {
    return "no prior run";
  }

  if (value === 0) {
    return "even with prior run";
  }

  return value < 0 ? `${Math.abs(value)} better than prior` : `${value} higher than prior`;
}

function targetDifficultyClass(target) {
  if (target.average_balls_to_hit === null || target.average_balls_to_hit === undefined) {
    return "noData";
  }

  const classes = [];
  if (target.average_balls_to_hit >= 3) {
    classes.push("hard");
  }

  if (target.average_balls_to_hit <= 1.5) {
    classes.push("sharp");
  }

  if ((target.attempts || 0) < 3) {
    classes.push("lowSample");
  }

  return classes.join(" ");
}

function runTargetClass(target) {
  if (!target || !target.attempts) {
    return "noData";
  }

  const classes = [];
  if (target.attempts >= 3) {
    classes.push("hard");
  }

  if (target.hit && target.attempts <= 1) {
    classes.push("sharp");
  }

  return classes.join(" ");
}

function targetByNumber(targets) {
  return new Map(targets.map((target) => [target.target_number, target]));
}

function compactMetric(value) {
  if (value === null || value === undefined) {
    return "-";
  }

  return formatNumber(value);
}

function codeSnapshotUrl(era, source = {}) {
  const sourceEra = resolveAppEra(source);
  if (sourceEra.id === era.id && source.app_git_sha) {
    return codeUrlForSha(source.app_git_sha);
  }

  return era.codeUrl;
}

function EraBadge({ era }) {
  return <span className={`eraBadge eraBadge-${era.id}`}>{era.title} era</span>;
}

function EraSnapshot({ era }) {
  return (
    <div
      className={`eraSnapshot eraSnapshot-${era.snapshotKind}`}
      role="img"
      aria-label={`${era.title} visual snapshot`}
    >
      <div className="snapshotTopbar">
        <span />
        <span />
        <span />
      </div>
      {era.snapshotKind === "first-live" ? (
        <div className="snapshotFirstLive">
          <div>
            <small>Observer Mode</small>
            <strong>Chip Tracker</strong>
          </div>
          <div className="snapshotStatGrid">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="snapshotList">
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : null}
      {era.snapshotKind === "polish-fonts" ? (
        <div className="snapshotPolish">
          <strong>2,142</strong>
          <span>balls tracked</span>
          <div className="snapshotScoreGrid">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : null}
      {era.snapshotKind === "net-map" ? (
        <div className="snapshotNet">
          <div className="snapshotNetOval">
            {[1, 3, 8, 5, 9, 6, 7, 4, 2].map((target) => (
              <span className={`snapshotTarget snapshotTarget-${target}`} key={target}>
                {target}
              </span>
            ))}
          </div>
        </div>
      ) : null}
      {era.snapshotKind === "era-timeline" ? (
        <div className="snapshotEra">
          <div>
            <strong>App Evolution</strong>
            <span />
          </div>
          <ol>
            <li />
            <li />
            <li />
          </ol>
        </div>
      ) : null}
    </div>
  );
}

function AppEvolutionTimeline({ build }) {
  return (
    <section className="appEvolutionPanel" id="evolution">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">App Evolution</p>
          <h2>Product memory</h2>
        </div>
        <span>visual provenance</span>
      </div>
      <p className="evolutionIntro">
        Sessions keep a small record of the product era that created them, so the practice
        history can show both training progress and app progress.
      </p>
      <ol className="eraTimeline">
        {APP_ERAS.map((era) => {
          const codeUrl = codeSnapshotUrl(era, build);
          return (
            <li className="eraTimelineItem" key={era.id}>
              <EraSnapshot era={era} />
              <div className="eraTimelineCopy">
                <div>
                  <span>{era.dateLabel}</span>
                  <strong>{era.title}</strong>
                </div>
                <p>{era.summary}</p>
                <small>{era.visibleFeature}</small>
                {codeUrl ? (
                  <a href={codeUrl} rel="noreferrer" target="_blank">
                    View code snapshot
                  </a>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function SegmentedControl({ label, options, value, onChange }) {
  return (
    <div className="segmentedBlock" aria-label={label}>
      <span>{label}</span>
      <div className="segmentedControl">
        {options.map((option) => (
          <button
            aria-pressed={option.key === value}
            className={option.key === value ? "active" : ""}
            key={option.key}
            onClick={() => onChange(option.key)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, detail }) {
  return (
    <div className="statCard">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

function EmptyState({ children }) {
  return <p className="emptyState">{children}</p>;
}

function formatMonthDay(value) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric"
  }).format(new Date(value));
}

function sessionTitle(session) {
  if (!session) {
    return "Session";
  }

  return formatDateTime(session.started_at);
}

function getSessionIdFromPath(pathname) {
  const match = pathname.match(/^\/sessions\/([^/]+)$/);
  return match ? decodeURIComponent(match[1]) : null;
}

function VolumeBars({ days = [] }) {
  const visibleDays = days.slice(0, 14).reverse();
  const maxBalls = Math.max(...visibleDays.map((day) => day.balls), 1);

  if (!visibleDays.length) {
    return <EmptyState>No volume chart yet.</EmptyState>;
  }

  return (
    <div className="volumeBars" aria-label="Recent practice volume">
      {visibleDays.map((day) => {
        const height = Math.max(8, Math.round((day.balls / maxBalls) * 100));
        return (
          <div className="volumeBarColumn" key={day.date}>
            <span className="volumeBarValue">{formatNumber(day.balls)}</span>
            <span className="volumeBarTrack">
              <span className="volumeBarFill" style={{ "--barHeight": `${height}%` }} />
            </span>
            <span className="volumeBarLabel">{formatMonthDay(day.date)}</span>
          </div>
        );
      })}
    </div>
  );
}

function CompletionTrend({ runs = [] }) {
  const visibleRuns = runs.slice(0, 6).reverse();
  const bestScore = Math.min(...visibleRuns.map((run) => run.score), Infinity);

  if (!visibleRuns.length) {
    return <EmptyState>No completion trend yet.</EmptyState>;
  }

  return (
    <ol className="scoreTrend" aria-label="Recent Target Completion scores">
      {visibleRuns.map((run) => (
        <li className={run.score === bestScore ? "best" : ""} key={run.id}>
          <span>{formatMonthDay(run.ended_at || run.started_at)}</span>
          <strong>{run.score}</strong>
          <small>{run.variant}</small>
        </li>
      ))}
    </ol>
  );
}

function TargetNetMap({ mode = "performance", rangeLabel, run, targets = [] }) {
  const performanceTargets = targetByNumber(targets);
  const runTargets = targetByNumber(run?.targets || []);
  const isLastRun = mode === "last_run";
  const mapLabel = isLastRun
    ? run
      ? `${run.variant} run / ${formatMaybeNumber(run.score)} balls`
      : "No completed run"
    : `${rangeLabel} / avg balls to hit`;

  return (
    <div className="netMapWrap">
      <svg className="netMap" role="img" aria-label={`Chipping net target map, ${mapLabel}`} viewBox="0 0 100 100">
        <defs>
          <pattern
            id="netMesh"
            width="4"
            height="4"
            patternTransform="rotate(38)"
            patternUnits="userSpaceOnUse"
          >
            <path d="M0 0 L0 4" />
          </pattern>
        </defs>
        <ellipse className="netBody" cx="50" cy="54" rx="46" ry="42" />
        <ellipse className="netInnerRim" cx="50" cy="54" rx="43" ry="38" />
        {NET_MESH_LINES.map((x) => (
          <path className="netStrand" d={`M${x} 17 C${x - 4} 36 ${x + 4} 68 ${x} 92`} key={x} />
        ))}
        <path className="netBase" d="M17 91 C29 98 71 98 83 91" />
        {chippingNetTargetsLayout.targets.map((layoutTarget) => {
          const target = performanceTargets.get(layoutTarget.id) || {
            target_number: layoutTarget.id,
            average_balls_to_hit: null,
            attempts: 0,
            hit_rate: null
          };
          const runTarget = runTargets.get(layoutTarget.id);
          const value = isLastRun ? runTarget?.attempts : target.average_balls_to_hit;
          const subValue = isLastRun
            ? runTarget?.hit
              ? "hit"
              : "open"
            : target.attempts
              ? `${target.attempts} att`
              : "no reps";
          const stateClass = isLastRun ? runTargetClass(runTarget) : targetDifficultyClass(target);
          const numberX = layoutTarget.x + layoutTarget.num_dx * layoutTarget.r;
          const numberY = layoutTarget.y + layoutTarget.num_dy * layoutTarget.r;

          return (
            <g className={`netTargetGroup ${stateClass}`} key={layoutTarget.id}>
              <g
                className="netTarget"
                style={{ "--target-color": layoutTarget.color }}
                transform={`translate(${layoutTarget.x} ${layoutTarget.y})`}
              >
                <title>
                  {isLastRun
                    ? `Target ${layoutTarget.id}: ${formatMaybeNumber(value)} balls in last run`
                    : `Target ${layoutTarget.id}: ${formatMaybeNumber(value)} average balls to hit`}
                </title>
                <circle className="netTargetShadow" r={layoutTarget.r + 1.4} />
                <circle className="netTargetRing" r={layoutTarget.r} />
                <circle className="netTargetMesh" r={Math.max(1, layoutTarget.r - 1.5)} />
                <text className="netTargetValue" textAnchor="middle" y="-0.4">
                  {compactMetric(value)}
                </text>
                <text className="netTargetSubvalue" textAnchor="middle" y="4.2">
                  {subValue}
                </text>
              </g>
              <text className="netTargetNumber" textAnchor="middle" x={numberX} y={numberY}>
                {layoutTarget.id}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="netMapReadout">
        <span>{mapLabel}</span>
        <span>{isLastRun ? "balls per target" : "dimmed targets need more reps"}</span>
      </div>
    </div>
  );
}

function SessionCard({ session }) {
  const era = resolveAppEra(session);

  return (
    <a className="sessionCardLink" href={`/sessions/${session.id}`}>
      <span>
        <strong>{sessionTitle(session)}</strong>
        <small>
          {formatNumber(session.ball_count)} balls / {formatDurationSeconds(session.duration_seconds)}
        </small>
        <EraBadge era={era} />
      </span>
      <SessionStatusPill status={session.status} />
    </a>
  );
}

function ObserverDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState(null);
  const [selectedRange, setSelectedRange] = useState("30d");
  const [targetMode, setTargetMode] = useState("performance");

  useEffect(() => {
    let ignore = false;

    async function loadStats() {
      setLoading(true);
      setError("");

      try {
        const rangedPath = (path) => publicStatsPath(path, selectedRange);
        const [overview, volume, accuracy, targets, completion, sessions, build] = await Promise.all([
          api(rangedPath("/api/public/overview")),
          api(rangedPath("/api/public/volume")),
          api(rangedPath("/api/public/accuracy")),
          api(rangedPath("/api/public/targets")),
          api(rangedPath("/api/public/completion")),
          api(rangedPath("/api/public/sessions")),
          api("/api/public/build")
        ]);

        if (!ignore) {
          setStats({ overview, volume, accuracy, targets, completion, sessions, build });
        }
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

    loadStats();
    return () => {
      ignore = true;
    };
  }, [selectedRange]);

  const overview = stats?.overview;
  const volume = stats?.volume;
  const accuracy = stats?.accuracy;
  const targets = stats?.targets?.targets || [];
  const hardestTargets = stats?.targets?.hardest_targets || [];
  const easiestTargets = stats?.targets?.easiest_targets || [];
  const completionRuns = stats?.completion?.completed_runs || [];
  const recentSessions = stats?.sessions?.sessions || [];
  const sourceTotals = Object.entries(volume?.source_totals || {});
  const build = stats?.build;
  const activeRange = rangeOption(selectedRange);
  const latestCompletionRun = completionRuns[0] || null;

  return (
    <main className="shell dashboardShell">
      <header className="siteTopbar">
        <a className="brandMark" href="/">
          <span>Chip</span>
          <strong>Tracker</strong>
        </a>
        <div className="siteNav">
          <a href="#sessions">Sessions</a>
          <a href="#targets">Targets</a>
          <a className="buildLink" href="#evolution">
            Evolution
          </a>
          <a className="primaryAction" href="/me/login">
            Log Practice
          </a>
        </div>
      </header>

      {loading ? <p className="muted">Loading...</p> : null}
      {error ? <p className="pageError">{error}</p> : null}

      {overview ? (
        <>
          <section className="dashboardControls">
            <SegmentedControl
              label="Window"
              onChange={setSelectedRange}
              options={DASHBOARD_RANGES}
              value={selectedRange}
            />
          </section>

          <section className="dashboardHero">
            <div className="heroCopy">
              <p className="eyebrow">Public training dashboard</p>
              <h1>
                {formatNumber(overview.total_balls)} balls {activeRange.heroSuffix}
              </h1>
              <p>
                Indoor chipping practice at {overview.practice_days} practice{" "}
                {overview.practice_days === 1 ? "day" : "days"} and{" "}
                {formatNumber(overview.completed_target_completion_runs)} completed 1-9 runs.
              </p>
            </div>
            <div className="heroScoreboard">
              <StatCard
                label={activeRange.label}
                value={`${formatNumber(overview.total_balls)} balls`}
                detail={
                  overview.latest_practice_at
                    ? `Last ${formatDateTime(overview.latest_practice_at)}`
                    : "No practice logged"
                }
              />
              <StatCard label="Practice days" value={formatNumber(overview.practice_days)} />
              <StatCard
                label="Best 1-9"
                value={formatMaybeNumber(overview.best_completion_score)}
                detail="balls"
              />
              <StatCard
                label="Avg session"
                value={formatMaybeNumber(overview.average_balls_per_completed_session)}
                detail="balls"
              />
            </div>
          </section>

          <section className="dashboardPanels">
            <article className="dataPanel volumePanel">
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Volume</p>
                  <h2>Recent work</h2>
                </div>
                <span>{activeRange.label}</span>
              </div>
              <VolumeBars days={volume?.daily || []} />
              <div className="sourceTotals">
                {sourceTotals.map(([source, total]) => (
                  <div key={source}>
                    <span>{sourceLabel(source)}</span>
                    <strong>{formatNumber(total)}</strong>
                  </div>
                ))}
              </div>
              {!sourceTotals.length ? <EmptyState>No logged volume yet.</EmptyState> : null}
            </article>

            <article className="dataPanel completionPanel">
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Target Completion</p>
                  <h2>1-9 trend</h2>
                </div>
                <span>lower is better</span>
              </div>
              <div className="scoreLine heroScore">
                <strong>{formatMaybeNumber(stats.completion.latest_score)}</strong>
                <span>
                  latest / {scoreDeltaLabel(stats.completion.score_delta_from_previous)}
                </span>
              </div>
              <CompletionTrend runs={completionRuns} />
              <div className="miniMetricRow">
                <span>Best {formatMaybeNumber(stats.completion.best_score)}</span>
                <span>Median {formatMaybeNumber(stats.completion.median_score)}</span>
                <span>Hit rate {formatPercent(accuracy?.hit_rate)}</span>
              </div>
            </article>

            <article className="dataPanel targetPanel" id="targets">
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Targets</p>
                  <h2>Net map</h2>
                </div>
                <span>{targetMode === "last_run" ? "last run" : "avg balls to hit"}</span>
              </div>
              <SegmentedControl
                label="Map"
                onChange={setTargetMode}
                options={TARGET_MAP_MODES}
                value={targetMode}
              />
              <TargetNetMap
                mode={targetMode}
                rangeLabel={activeRange.label}
                run={latestCompletionRun}
                targets={targets}
              />
              {targetMode === "last_run" && latestCompletionRun ? (
                <div className="miniMetricRow">
                  <span>Score {formatMaybeNumber(latestCompletionRun.score)}</span>
                  <span>{latestCompletionRun.variant}</span>
                  <span>{formatDateTime(latestCompletionRun.ended_at || latestCompletionRun.started_at)}</span>
                </div>
              ) : null}
              {targetMode === "performance" && (hardestTargets.length || easiestTargets.length) ? (
                <div className="targetInsightGrid">
                  <div className="weakTargetRow">
                    <span className="chipLabel">Hardest</span>
                    {hardestTargets.map((target) => (
                      <span key={target.target_number}>
                        T{target.target_number}: {target.average_balls_to_hit}
                      </span>
                    ))}
                  </div>
                  <div className="sharpTargetRow">
                    <span className="chipLabel">Sharpest</span>
                    {easiestTargets.map((target) => (
                      <span key={target.target_number}>
                        T{target.target_number}: {target.average_balls_to_hit}
                      </span>
                    ))}
                  </div>
                </div>
              ) : targetMode === "performance" ? (
                <EmptyState>No target history yet.</EmptyState>
              ) : null}
            </article>
          </section>

          <section className="sessionShowcase" id="sessions">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Sessions</p>
                <h2>Recent practice blocks</h2>
              </div>
              <span>{formatNumber(overview.total_sessions)} total</span>
            </div>
            <div className="sessionCardGrid">
              {recentSessions.slice(0, 6).map((session) => (
                <SessionCard key={session.id} session={session} />
              ))}
            </div>
            {recentSessions.length ? null : <EmptyState>No sessions yet.</EmptyState>}
          </section>

          <AppEvolutionTimeline build={build} />
        </>
      ) : null}
    </main>
  );
}

function SessionDetail() {
  const sessionId = getSessionIdFromPath(window.location.pathname);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadSession() {
      setLoading(true);
      setError("");

      try {
        const response = await api(`/api/public/sessions/${sessionId}`);
        if (!ignore) {
          setDetail(response);
        }
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

    loadSession();
    return () => {
      ignore = true;
    };
  }, [sessionId]);

  const session = detail?.session;
  const buckets = detail?.buckets || [];
  const games = detail?.games || [];
  const sourceTotals = Object.entries(detail?.source_totals || {});
  const sessionEra = resolveAppEra(detail?.provenance || {});
  const sessionCodeUrl = codeSnapshotUrl(sessionEra, detail?.provenance || {});

  return (
    <main className="shell dashboardShell">
      <header className="siteTopbar">
        <a className="brandMark" href="/">
          <span>Chip</span>
          <strong>Tracker</strong>
        </a>
        <div className="siteNav">
          <a href="/">Dashboard</a>
          <a className="primaryAction" href="/me/login">
            Log Practice
          </a>
        </div>
      </header>

      {loading ? <p className="muted">Loading...</p> : null}
      {error ? <p className="pageError">{error}</p> : null}

      {session ? (
        <>
          <section className="sessionHero">
            <div>
              <p className="eyebrow">Session detail</p>
              <h1>{formatDateTime(session.started_at)}</h1>
              <p>
                {formatNumber(session.ball_count)} balls across {formatNumber(session.bucket_count)}{" "}
                {session.bucket_count === 1 ? "bucket" : "buckets"} at{" "}
                {session.default_distance_ft} ft.
              </p>
            </div>
            <div className="sessionHeroStats">
              <StatCard label="Duration" value={formatDurationSeconds(session.duration_seconds)} />
              <StatCard label="Games" value={formatNumber(session.game_count)} />
              <StatCard label="Default" value={`${session.default_club} / ${session.default_distance_ft} ft`} />
              <div className="statCard">
                <span>Status</span>
                <SessionStatusPill status={session.status} />
              </div>
            </div>
          </section>

          <section className="sessionDetailGrid">
            <article className="dataPanel sessionBucketsPanel">
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Buckets</p>
                  <h2>Practice volume</h2>
                </div>
                <span>{formatNumber(session.ball_count)} balls</span>
              </div>
              {sourceTotals.length ? (
                <div className="sourceTotals">
                  {sourceTotals.map(([source, total]) => (
                    <div key={source}>
                      <span>{sourceLabel(source)}</span>
                      <strong>{formatNumber(total)}</strong>
                    </div>
                  ))}
                </div>
              ) : null}
              {buckets.length ? (
                <ol className="bucketTimeline">
                  {buckets.map((bucket, index) => (
                    <li key={bucket.id}>
                      <span>{index + 1}</span>
                      <div>
                        <strong>{formatNumber(bucket.ball_count)} balls</strong>
                        <small>
                          {sourceLabel(bucket.source)} / {bucket.club} / {bucket.distance_ft} ft
                        </small>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <EmptyState>No bucket volume recorded for this session.</EmptyState>
              )}
            </article>

            <article className="dataPanel sessionGamesPanel">
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Games</p>
                  <h2>Target Completion</h2>
                </div>
                <span>{formatNumber(games.length)} runs</span>
              </div>
              {games.length ? (
                <div className="sessionGameStack">
                  {games.map((game) => (
                    <div className="sessionGameCard" key={game.id}>
                      <div className="sessionGameHeader">
                        <div>
                          <strong>{game.variant} 1-9</strong>
                          <small>
                            {game.status} / {formatDurationSeconds(game.duration_seconds)}
                          </small>
                        </div>
                        <span>{game.score} balls</span>
                      </div>
                      <ol className="sessionTargetMap">
                        {game.targets.map((target) => (
                          <li className={target.hit ? "completed" : ""} key={target.target_number}>
                            <strong>{target.target_number}</strong>
                            <span>{target.attempts}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState>No structured game in this session.</EmptyState>
              )}
            </article>

            <article className="dataPanel provenancePanel">
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Created during</p>
                  <h2>{sessionEra.title}</h2>
                </div>
                <span>{sessionEra.shortLabel}</span>
              </div>
              <EraSnapshot era={sessionEra} />
              <p className="provenanceSummary">{sessionEra.summary}</p>
              <div className="provenanceReadout">
                <div>
                  <span>App era</span>
                  <strong>{sessionEra.title}</strong>
                  {sessionCodeUrl ? (
                    <a href={sessionCodeUrl} rel="noreferrer" target="_blank">
                      View code snapshot
                    </a>
                  ) : null}
                </div>
                <div>
                  <span>Visible feature</span>
                  <strong>{sessionEra.visibleFeature}</strong>
                </div>
                <div>
                  <span>Code trail</span>
                  <strong>{sessionCodeUrl ? "Snapshot available" : "not captured yet"}</strong>
                </div>
              </div>
            </article>
          </section>
        </>
      ) : null}
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

function QuickLogPanel({ activeSession, buckets, disabled, sessionTotal, onQuickLog }) {
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
          <div className="quickLogSummary">
            <span>Session total</span>
            <strong>{formatNumber(sessionTotal)} balls</strong>
          </div>
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
              Log Custom
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
  const completedCount = activeGame.completed_targets.length;

  return (
    <div className="targetGamePanel activeTargetGame">
      <div className="gameHeader">
        <div>
          <p className="eyebrow">Target Completion</p>
          <h2>{currentTarget ? `Target ${currentTarget.target_number}` : "Complete"}</h2>
        </div>
        <SessionStatusPill status={activeGame.variant} />
      </div>

      <div className="progressRail" aria-label="Target Completion progress">
        <span style={{ width: `${Math.round((completedCount / 9) * 100)}%` }} />
      </div>

      <div className="gameStats">
        <div>
          <span>Progress</span>
          <strong>{completedCount}/9</strong>
        </div>
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

function OwnerToolsPanel() {
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadPrompt() {
    setBusy(true);
    setError("");

    try {
      const response = await api("/api/prompts/practice-summary");
      setPrompt(response.prompt);
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="ownerToolsPanel">
      <div className="historyHeader">
        <p className="eyebrow">Output</p>
      </div>
      <div className="exportGrid">
        <a className="secondaryAction" href="/api/export/json">
          Export JSON
        </a>
        <a className="secondaryAction" href="/api/export/csv">
          Export CSV
        </a>
      </div>
      <button className="secondaryButton" type="button" onClick={loadPrompt} disabled={busy}>
        {busy ? "Building..." : "Prompt Helper"}
      </button>
      {error ? <p className="formError">{error}</p> : null}
      {prompt ? (
        <textarea className="promptBox" readOnly value={prompt} aria-label="Prompt helper" />
      ) : null}
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
    const nextState = { active, history, game, buckets };

    setActiveSession(active);
    setActiveBuckets(buckets);
    setActiveGame(game);
    setSessions(history);
    return nextState;
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
      setQuickLogMessage("Session started");
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
      setQuickLogMessage(`Session ended: ${formatNumber(activeBallTotal)} balls`);
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
      setQuickLogMessage("Session abandoned");
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
      const refreshed = await refreshSessions();
      if (result.session.status === "active") {
        window.history.replaceState({}, "", "/me/session/active");
      }
      const refreshedSessionTotal = refreshed.buckets.reduce(
        (total, bucket) => total + bucket.ball_count,
        0
      );
      if (result.standalone_session_created) {
        setQuickLogMessage(`Logged standalone +${result.bucket.ball_count}`);
      } else if (result.active_session_created) {
        setQuickLogMessage(
          `Started session and logged +${result.bucket.ball_count} - ${formatNumber(
            refreshedSessionTotal
          )} balls total`
        );
      } else {
        setQuickLogMessage(
          `Logged +${result.bucket.ball_count} - ${formatNumber(refreshedSessionTotal)} balls total`
        );
      }
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
      setGameMessage(`Started ${variant} 1-9`);
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
      setGameMessage("Bucket ended / retrieve");
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

      {activeSession ? (
        <section className="liveStrip" aria-label="Active practice status">
          <div>
            <span>Session</span>
            <strong>{sessionDuration(activeSession)}</strong>
          </div>
          <div>
            <span>Balls</span>
            <strong>{formatNumber(activeBallTotal)}</strong>
          </div>
          <div>
            <span>Game</span>
            <strong>
              {activeGame
                ? `${activeGame.completed_targets.length}/9 ${activeGame.variant}`
                : "Open"}
            </strong>
          </div>
          <div>
            <span>Default</span>
            <strong>
              {activeSession.default_club} / {activeSession.default_distance_ft} ft
            </strong>
          </div>
        </section>
      ) : null}

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
            sessionTotal={activeBallTotal}
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

        <OwnerToolsPanel />
      </section>

      <div className="toastStack" aria-live="polite">
        {quickLogMessage ? <p className="successMessage">{quickLogMessage}</p> : null}
        {gameMessage ? <p className="successMessage">{gameMessage}</p> : null}
        {error ? <p className="pageError">{error}</p> : null}
      </div>
    </main>
  );
}

export default function App() {
  if (getSessionIdFromPath(window.location.pathname)) {
    return <SessionDetail />;
  }

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

  return <ObserverDashboard />;
}
