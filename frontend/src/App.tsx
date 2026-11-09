import {
  Check,
  ChevronRight,
  Layers3,
  LoaderCircle,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  UploadCloud,
  X,
  ChartScatter,
  CircleDot,
} from "lucide-react";
import { useWorkbench } from "./state/WorkbenchContext";
import { ImportView } from "./features/import/ImportView";
import { ModelingView } from "./features/modeling/ModelingView";
import { ResultsView } from "./features/results/ResultsView";
import { ConnectionDialog } from "./features/connections/ConnectionDialog";
const steps = [
  { label: "Import", icon: UploadCloud },
  { label: "Modellierung", icon: SlidersHorizontal },
  { label: "Ergebnisse", icon: ChartScatter },
];
export default function App() {
  const {
    token,
    step,
    setStep,
    cleaned,
    params,
    result,
    job,
    error,
    setError,
    notice,
    setNotice,
    settings,
    setSettings,
    active,
  } = useWorkbench();
  return (
    <>
      <header className="topbar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setStep(0);
          }}
        >
          <span className="brand-icon">
            <Layers3 size={21} />
          </span>
          BERTopic
        </a>
        <button className="connection" onClick={() => setSettings(true)}>
          <span className={token ? "status-dot" : "status-dot offline"} />
          {token ? "Lokal verbunden" : "Verbindung wird aufgebaut"}
          <Settings2 size={15} />
        </button>
      </header>
      <main>
        <div className="workspace-heading">
          <div>
            <h1>#NDRfragt Topic Modeling</h1>
          </div>
          <span className="local-badge">
            <ShieldCheck size={15} />
            Lokales Modelltraining
          </span>
        </div>
        <nav className="step-nav" aria-label="Analyseschritte">
          {steps.map((item, index) => {
            const Icon = item.icon,
              done = index === 0 ? !!cleaned : index === 1 ? !!result : false;
            return (
              <button
                key={item.label}
                className={step === index ? "step active-step" : "step"}
                disabled={(index === 1 && !cleaned) || (index === 2 && !result)}
                onClick={() => setStep(index)}
                aria-current={step === index ? "step" : undefined}
              >
                <span className="step-number">
                  {done ? (
                    <Check size={14} />
                  ) : (
                    String(index + 1).padStart(2, "0")
                  )}
                </span>
                <Icon size={17} />
                {item.label}
                <ChevronRight size={15} className="step-arrow" />
              </button>
            );
          })}
        </nav>
        {error && (
          <div className="alert error" role="alert">
            <span>{error}</span>
            <button
              className="icon-button"
              aria-label="Fehler schließen"
              onClick={() => setError("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
        {notice && (
          <div className="alert notice">
            <span>{notice}</span>
            <button
              className="icon-button"
              aria-label="Hinweis schließen"
              onClick={() => setNotice("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
        {(active || job.status === "failed") && (
          <section className="job-card" aria-live="polite">
            <div className="job-title">
              {active ? (
                <LoaderCircle size={18} className="spin" />
              ) : (
                <CircleDot size={18} />
              )}
              <strong>{job.message}</strong>
              <span>{job.progress}%</span>
            </div>
            <progress max={100} value={job.progress} />
            {job.error && <p className="error-text">{job.error}</p>}
            <p className="muted">
              {active
                ? "Der Vorgang läuft unabhängig von der geöffneten Ansicht."
                : "Bisherige Ergebnisse bleiben erhalten."}
            </p>
          </section>
        )}
        {step === 0 && <ImportView />}
        {step === 1 && params && cleaned && <ModelingView />}
        {step === 2 && result && <ResultsView />}
      </main>
      {settings && <ConnectionDialog />}
    </>
  );
}
