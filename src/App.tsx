import {
  Check,
  ChevronRight,
  Settings2,
  SlidersHorizontal,
  UploadCloud,
  X,
  ChartScatter,
  ListTree,
} from "lucide-react";
import { TrainingProgress } from "./components/TrainingProgress";
import { useWorkbench } from "./context/WorkbenchContext";
import { ImportPage } from "./pages/ImportPage";
import { ModelingPage } from "./pages/ModelingPage";
import { ResultsPage } from "./pages/ResultsPage";
import { OpenAIConnectionDialog } from "./components/OpenAIConnectionDialog";
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
    resultTab,
    setResultTab,
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
          Topic Modeling
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
            <h1 className="app-title">
              <img
                className="app-mascot"
                src="/schwalbe.svg"
                alt=""
                aria-hidden="true"
              />
              <span>#NDRfragt Themenfinder</span>
            </h1>
          </div>
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
        {step === 2 && result && (
          <nav className="analysis-nav" aria-label="Ergebnisansichten">
            <div className="segmented">
              {[
                { id: "topics", label: "Themenübersicht", icon: ListTree },
                { id: "charts", label: "Visualisierungen", icon: ChartScatter },
              ].map((item) => (
                <button
                  key={item.id}
                  className={resultTab === item.id ? "selected" : ""}
                  aria-current={resultTab === item.id ? "page" : undefined}
                  onClick={() => setResultTab(item.id)}
                >
                  <item.icon size={17} aria-hidden="true" />
                  {item.label}
                </button>
              ))}
            </div>
          </nav>
        )}

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
          <TrainingProgress job={job} namingEnabled={!!params?.name_topics} />
        )}
        {step === 0 && <ImportPage />}
        {step === 1 && params && cleaned && <ModelingPage />}
        {step === 2 && result && <ResultsPage />}
      </main>
      {settings && <OpenAIConnectionDialog />}
    </>
  );
}
