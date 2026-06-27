import "./styles.css";

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
          <h2>Practice stats will appear here.</h2>
          <p>
            This scaffold keeps the public view as the default entry point while the data
            model and logging workflow are built in later milestones.
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

function MeLoginPlaceholder() {
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
          <p className="eyebrow">Owner login placeholder</p>
          <h2>Authentication starts in the next milestone.</h2>
          <p>
            This screen reserves the owner entry point without enabling write actions yet.
          </p>
        </div>
        <form className="loginForm">
          <label htmlFor="pin">PIN</label>
          <input id="pin" name="pin" type="password" placeholder="Not wired yet" disabled />
          <button type="button" disabled>
            Enter Me Mode
          </button>
        </form>
      </section>
    </main>
  );
}

export default function App() {
  if (window.location.pathname === "/me/login") {
    return <MeLoginPlaceholder />;
  }

  return <ObserverPlaceholder />;
}
