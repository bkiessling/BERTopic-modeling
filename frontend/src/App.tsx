import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowLeft,
  ArrowUpRight,
  Check,
  ChevronRight,
  Download,
  FileSpreadsheet,
  FlaskConical,
  Layers3,
  LoaderCircle,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UploadCloud,
  X,
  ChartScatter,
  Network,
  Type,
  RotateCcw,
  CircleDot,
  Link2,
} from "lucide-react";
import { api, post, defaults, idleJob } from "./api";
import type { Job, Params, Row } from "./api";
import {
  DataTable,
  Field,
  Help,
  Plot,
  Range,
  Select,
  MultiSelect,
} from "./components";
const steps = [
  { label: "Import", icon: UploadCloud },
  { label: "Modellierung", icon: SlidersHorizontal },
  { label: "Ergebnisse", icon: ChartScatter },
];
const options = (values: string[]) =>
  values.map((value) => ({ value, label: value }));
const message = (e: unknown) =>
  e instanceof Error ? e.message : "Ein unerwarteter Fehler ist aufgetreten.";
export default function App() {
  const [token, setToken] = useState(""),
    [caps, setCaps] = useState<Row | null>(null),
    [step, setStep] = useState(0);
  const [uploaded, setUploaded] = useState<Row | null>(null),
    [cleaned, setCleaned] = useState<Row | null>(null),
    [params, setParams] = useState<Params | null>(null),
    [result, setResult] = useState<Row | null>(null);
  const [job, setJob] = useState<Job>(idleJob),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [textCols, setTextCols] = useState<string[]>([]),
    [idCol, setIdCol] = useState("ID generieren"),
    [sample, setSample] = useState(100),
    [stopwords, setStopwords] = useState(""),
    [file, setFile] = useState<File | null>(null);
  const [resultTab, setResultTab] = useState("topics"),
    [chartKind, setChartKind] = useState("similarity"),
    [chart, setChart] = useState<any>(null),
    [chartError, setChartError] = useState("");
  const [selectedTopics, setSelectedTopics] = useState<number[]>([]),
    [method, setMethod] = useState("umap"),
    [revision, setRevision] = useState(0),
    [documents, setDocuments] = useState<Row | null>(null);
  const [search, setSearch] = useState(""),
    [page, setPage] = useState(0),
    [grouped, setGrouped] = useState(false),
    [threshold, setThreshold] = useState(0.05),
    [settings, setSettings] = useState(false),
    [namingModel, setNamingModel] = useState("gpt-4.1-mini");
  const fileInput = useRef<HTMLInputElement>(null),
    completed = useRef(false),
    initializing = useRef<Promise<Row> | null>(null);
  const active = ["queued", "running"].includes(job.status),
    blocked = active || !!busy;
  const loadResults = useCallback(async (id: string) => {
    const value = await api("/results", id);
    setResult(value);
    setSelectedTopics(
      (value.topics as Row[])
        .filter((t) => t.Thema !== -1)
        .slice(0, 4)
        .map((t) => t.Thema),
    );
    setRevision((v) => v + 1);
    return value;
  }, []);
  useEffect(() => {
    let live = true;
    if (!initializing.current)
      initializing.current = (async () => {
        const capability = await api("/capabilities", "");
        let id = localStorage.getItem("themenstudio-workspace") || "",
          restored: Row | null = null;
        if (id) {
          try {
            restored = await api("/workspace", id);
          } catch {
            id = "";
          }
        }
        if (!id) {
          id = (await api("/workspaces", "", { method: "POST" })).id;
          localStorage.setItem("themenstudio-workspace", id);
        }
        return { capability, id, restored };
      })();
    initializing.current
      .then(async ({ capability, id, restored }) => {
        if (!live) return;
        setCaps(capability);
        setToken(id);
        setNamingModel(capability.default_naming_model);
        if (restored?.import_result) {
          setUploaded(restored.import_result);
          setTextCols(restored.text_columns || []);
          setIdCol(restored.id_column || "ID generieren");
          setSample(restored.preprocessing?.sample_percentage || 100);
          setStopwords(restored.preprocessing?.custom_stopwords || "");
        }
        if (restored?.clean_result) {
          setCleaned(restored.clean_result);
          setParams(
            defaults(
              restored.clean_result.defaults,
              capability.default_naming_model,
            ),
          );
        }
        if (restored?.has_results) {
          const previous = await loadResults(id);
          if (live) {
            setParams(previous.parameters);
            setNamingModel(
              previous.naming.model || previous.parameters.naming_model,
            );
            setStep(2);
          }
        }
        if (restored?.job) setJob(restored.job);
      })
      .catch((e) => {
        if (live) setError(message(e));
      });
    return () => {
      live = false;
    };
  }, [loadResults]);
  useEffect(() => {
    if (!active || !token) return;
    let live = true;
    completed.current = false;
    const timer = setInterval(async () => {
      try {
        const next = await api<Job>("/job", token);
        if (!live) return;
        if (next.status === "completed" && !completed.current) {
          completed.current = true;
          await loadResults(token);
          if (!live) return;
          setStep(2);
          setNotice(next.warning || "");
        }
        setJob(next);
      } catch (e) {
        if (live) setError(message(e));
      }
    }, 750);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [active, token, loadResults]);
  useEffect(() => {
    if (!result || step !== 2 || resultTab !== "documents") return;
    let live = true;
    const timer = setTimeout(() => {
      api(
        `/documents?page=${page}&search=${encodeURIComponent(search)}&grouped=${grouped}`,
        token,
      )
        .then((data) => {
          if (live) setDocuments(data);
        })
        .catch((e) => {
          if (live) setError(message(e));
        });
    }, 200);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [result, step, resultTab, page, search, grouped, token, revision]);
  useEffect(() => {
    if (!result || step !== 2 || resultTab !== "charts") return;
    let live = true;
    setChart(null);
    setChartError("");
    if (chartKind === "bars" && !selectedTopics.length) return;
    api(
      `/charts/${chartKind}?topics=${selectedTopics.join(",")}&method=${method}`,
      token,
    )
      .then((data) => {
        if (live) setChart(data);
      })
      .catch((e) => {
        if (live) setChartError(message(e));
      });
    return () => {
      live = false;
    };
  }, [
    result,
    step,
    resultTab,
    chartKind,
    selectedTopics,
    method,
    token,
    revision,
  ]);
  useEffect(() => {
    if (!settings) return;
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSettings(false);
      if (event.key === "Tab") {
        const items = document.querySelectorAll<HTMLElement>(
          "[role=dialog] button:not(:disabled),[role=dialog] select:not(:disabled),[role=dialog] a[href]",
        );
        const first = items[0],
          last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [settings]);
  async function perform(name: string, task: () => Promise<void>) {
    setBusy(name);
    setError("");
    try {
      await task();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy("");
    }
  }
  async function upload(next: File, delimiter?: string) {
    await perform("upload", async () => {
      const form = new FormData();
      form.append("file", next);
      if (delimiter) form.append("delimiter", delimiter);
      const data = await api("/import", token, { method: "POST", body: form });
      setUploaded(data);
      setFile(next);
      setTextCols(data.text_columns.slice(0, 1));
      setIdCol("ID generieren");
      setCleaned(null);
      setResult(null);
      setParams(null);
      setJob(idleJob);
      setNotice("");
    });
  }
  async function clean() {
    await perform("clean", async () => {
      const data = await api(
        "/clean",
        token,
        post({
          text_columns: textCols,
          id_column: idCol,
          sample_percentage: sample,
          custom_stopwords: stopwords,
        }),
      );
      setCleaned(data);
      setParams(defaults(data.defaults, namingModel));
      setResult(null);
      setJob(idleJob);
      setNotice("");
    });
  }
  function change(update: Partial<Params>) {
    setParams((old) => (old ? { ...old, ...update } : old));
  }
  async function startJob(path: string, body: unknown = {}) {
    await perform("job", async () => {
      completed.current = false;
      setJob(await api<Job>(path, token, post(body)));
      setNotice("");
    });
  }
  async function download() {
    await perform("export", async () => {
      const response = await fetch("/api/export", {
        headers: { "X-Workspace-ID": token },
      });
      if (!response.ok) throw new Error("Export konnte nicht erstellt werden.");
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = "bertopic-results.zip";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  }
  const modelOptions: Row[] = (caps?.models || []).filter((m: Row) =>
    m.languages.includes(params?.language || "Deutsch"),
  );
  const topics: Row[] = result?.topics || [],
    keywords: Row[] = result?.keywords || [];
  const idPreviewColumn =
    idCol === "ID generieren"
      ? textCols.includes("ID")
        ? "ID (generiert)"
        : "ID"
      : idCol;
  const sourcePreview: Row[] = (uploaded?.preview || []).map((row: Row) => {
    const selected: Row = {
      [idPreviewColumn]: idCol === "ID generieren" ? "" : row[idCol],
    };
    for (const column of textCols) selected[column] = row[column];
    return selected;
  });
  const invalid: string[] = [];
  if (params && cleaned) {
    if (cleaned.rows < 4)
      invalid.push("Mindestens vier bereinigte Texte erforderlich.");
    if (params.umap.n_neighbors >= cleaned.rows)
      invalid.push("Nachbarn müssen unter der Textanzahl liegen.");
    if (params.umap.n_components > cleaned.rows - 2)
      invalid.push(
        "Dimensionen müssen mindestens zwei unter der Textanzahl liegen.",
      );
    if (params.hdbscan.min_cluster_size > cleaned.rows)
      invalid.push("Clustergröße überschreitet die Textanzahl.");
    if (params.vectorizer.min_df > params.vectorizer.max_df)
      invalid.push("Minimale Häufigkeit überschreitet das Maximum.");
  }
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
          themncluster
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
          <div className="workspace-file">
            {uploaded ? (
              <>
                <FileSpreadsheet size={15} />
                <span>{uploaded.file_name}</span>
              </>
            ) : (
              <span>Neuer Arbeitsbereich</span>
            )}
          </div>
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
        {step === 0 && (
          <>
            <section className="section-heading">
              <div>
                <span className="section-kicker">01 / IMPORT</span>
                <h2>Daten importieren</h2>
              </div>
              <span className="quiet-chip">CSV & Excel</span>
            </section>
            <div className="import-grid">
              <section className="card upload-card">
                <div className="card-title">
                  <FileSpreadsheet size={18} />
                  <h3>Datenquelle</h3>
                </div>
                <input
                  ref={fileInput}
                  aria-label="CSV- oder Excel-Datei auswählen"
                  type="file"
                  accept=".csv,.xlsx"
                  hidden
                  onChange={(e) => {
                    if (e.target.files?.[0]) void upload(e.target.files[0]);
                  }}
                />
                <button
                  className="dropzone"
                  disabled={!token || blocked}
                  onClick={() => fileInput.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (token && !blocked && e.dataTransfer.files[0])
                      void upload(e.dataTransfer.files[0]);
                  }}
                >
                  <span className="upload-icon">
                    {busy === "upload" ? (
                      <LoaderCircle className="spin" size={25} />
                    ) : (
                      <UploadCloud size={25} />
                    )}
                  </span>
                  <strong>
                    {uploaded ? "Datei austauschen" : "Datei hier ablegen"}
                  </strong>
                  <span>
                    oder <b>Datei auswählen</b>
                  </span>
                  <small>.csv oder .xlsx · bis zu 25 MB</small>
                </button>
                {uploaded && (
                  <div className="file-loaded">
                    <span className="file-icon">
                      <FileSpreadsheet size={20} />
                    </span>
                    <div>
                      <strong>{uploaded.file_name}</strong>
                      <p>
                        {uploaded.rows.toLocaleString("de-DE")} Zeilen ·{" "}
                        {uploaded.columns.length} Spalten
                      </p>
                    </div>
                    <Check size={18} />
                  </div>
                )}
                {file?.name.toLowerCase().endsWith(".csv") && (
                  <Field label="CSV-Trennzeichen">
                    <Select
                      label="CSV-Trennzeichen"
                      value={uploaded?.delimiter || ","}
                      options={[
                        { value: ",", label: "Komma ( , )" },
                        { value: ";", label: "Semikolon ( ; )" },
                        { value: "\t", label: "Tabulator" },
                      ]}
                      disabled={blocked}
                      onChange={(value) => void upload(file, value)}
                    />
                  </Field>
                )}
              </section>
              <section className="card selection-card">
                <div className="card-title">
                  <Type size={18} />
                  <h3>Texte auswählen</h3>
                </div>
                {uploaded ? (
                  <>
                    <Field
                      label="Textspalten"
                      help="Mehrere Spalten werden zu einzelnen Textbeiträgen untereinander angeordnet."
                    >
                      <MultiSelect
                        label="Textspalten"
                        values={textCols}
                        options={uploaded.text_columns}
                        disabled={blocked}
                        onChange={(values) => {
                          setTextCols(values);
                          if (values.includes(idCol)) setIdCol("ID generieren");
                          setCleaned(null);
                        }}
                      />
                      {!uploaded.text_columns.length && (
                        <p className="error-text">
                          Keine Textspalten gefunden. Trennzeichen prüfen.
                        </p>
                      )}
                    </Field>
                    <Field
                      label="ID-Spalte"
                      help="Verbindet Texte mit den ursprünglichen Einträgen."
                    >
                      <Select
                        label="ID-Spalte"
                        value={idCol}
                        options={options([
                          "ID generieren",
                          ...uploaded.columns.filter(
                            (col: string) => !textCols.includes(col),
                          ),
                        ])}
                        disabled={blocked}
                        onChange={(v) => {
                          setIdCol(v);
                          setCleaned(null);
                        }}
                      />
                    </Field>
                    <div className="two-fields">
                      <Field label="Stichprobe (%)">
                        <input
                          aria-label="Stichprobe (%)"
                          type="number"
                          min={1}
                          max={100}
                          value={sample}
                          disabled={blocked}
                          onChange={(e) => {
                            setSample(+e.target.value);
                            setCleaned(null);
                          }}
                        />
                      </Field>
                      <Field
                        label="Zusätzliche Stopwörter"
                        help="Durch Komma getrennte Wörter oder Phrasen zum Entfernen."
                      >
                        <input
                          aria-label="Zusätzliche Stopwörter"
                          placeholder="z. B. newsletter, firma"
                          value={stopwords}
                          disabled={blocked}
                          onChange={(e) => {
                            setStopwords(e.target.value);
                            setCleaned(null);
                          }}
                        />
                      </Field>
                    </div>
                    <button
                      className="button secondary full"
                      disabled={
                        blocked ||
                        !textCols.length ||
                        sample < 1 ||
                        sample > 100
                      }
                      onClick={() => void clean()}
                    >
                      <Sparkles size={16} />
                      Daten bereinigen
                    </button>
                  </>
                ) : (
                  <div className="placeholder">
                    <span className="placeholder-glyph">
                      <Type size={28} />
                    </span>
                    <p>
                      Deine Textspalten erscheinen hier,
                      <br />
                      sobald eine Datei importiert ist.
                    </p>
                  </div>
                )}
              </section>
            </div>
            {(uploaded || cleaned) && (
              <section className="card preview-card">
                <div className="preview-heading">
                  <div>
                    <h3>
                      {cleaned ? "Bereit für die Analyse" : "Datenvorschau"}
                    </h3>
                    <p>
                      {cleaned
                        ? "Ausgewählte Originalspalten. Die bereinigten Texte sind darunter aufklappbar."
                        : "Ausgewählte Spalten · erste acht Zeilen."}
                    </p>
                  </div>
                  {cleaned && (
                    <span className="success-chip">
                      <Check size={13} />
                      Bereinigt
                    </span>
                  )}
                </div>
                {cleaned && (
                  <div className="mini-stats">
                    <div>
                      <strong>{cleaned.rows.toLocaleString("de-DE")}</strong>
                      <span>verwendbare Texte</span>
                    </div>
                    <div>
                      <strong>{cleaned.rows_before - cleaned.rows}</strong>
                      <span>entfernte Texte</span>
                    </div>
                    <div>
                      <strong>{cleaned.average_length}</strong>
                      <span>Ø Zeichen / Text</span>
                    </div>
                  </div>
                )}
                <DataTable rows={sourcePreview} />
                {cleaned && (
                  <details className="cleaned-preview">
                    <summary>Bereinigte Texte anzeigen</summary>
                    <DataTable
                      rows={cleaned.preview.map((row: Row) => ({
                        ID: row.id,
                        Text: row.text,
                      }))}
                    />
                  </details>
                )}
              </section>
            )}
            <div className="action-bar">
              <span>
                <ShieldCheck size={15} />
                Deine Daten werden lokal verarbeitet.
              </span>
              <button
                className="button primary"
                disabled={!cleaned || blocked}
                onClick={() => setStep(1)}
              >
                Weiter zur Modellierung
                <ArrowRight size={16} />
              </button>
            </div>
          </>
        )}
        {step === 1 && params && cleaned && (
          <>
            <section className="section-heading">
              <div>
                <span className="section-kicker">02 / MODELLIERUNG</span>
                <h2>Die richtigen Fragen an deine Texte.</h2>
                <p>
                  Starte mit den Voreinstellungen oder passe dein Modell gezielt
                  an.
                </p>
              </div>
              <span className="quiet-chip">
                <FileSpreadsheet size={14} />
                {cleaned.rows.toLocaleString("de-DE")} Texte
              </span>
            </section>
            <fieldset className="model-fieldset" disabled={blocked}>
              <div className="model-top-grid">
                <section className="card">
                  <div className="card-title">
                    <Layers3 size={18} />
                    <h3>Sprache & Embeddings</h3>
                    <Help title="Embeddings">
                      Das Sprachmodell übersetzt Texte in Bedeutungsvektoren.
                      Deutsche Texte brauchen ein deutschfähiges Modell.
                    </Help>
                  </div>
                  <div className="model-select-grid">
                    <Field label="Sprache">
                      <Select
                        label="Sprache"
                        value={params.language}
                        options={options(["Deutsch", "Englisch"])}
                        onChange={(language) =>
                          change({
                            language,
                            embedding_model:
                              language === "Deutsch"
                                ? "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                                : "sentence-transformers/all-MiniLM-L6-v2",
                          })
                        }
                      />
                    </Field>
                    <Field label="Embedding-Modell">
                      <Select
                        label="Embedding-Modell"
                        value={params.embedding_model}
                        options={modelOptions.map((m) => ({
                          value: m.id,
                          label: m.label,
                        }))}
                        onChange={(embedding_model) =>
                          change({ embedding_model })
                        }
                      />
                    </Field>
                  </div>
                  <div className="model-note">
                    <span className="dot violet" />
                    <p>
                      {
                        modelOptions.find(
                          (m) => m.id === params.embedding_model,
                        )?.description
                      }
                    </p>
                    <a
                      href={`https://huggingface.co/${params.embedding_model}`}
                      target="_blank"
                      rel="noreferrer"
                      aria-label="Modellkarte öffnen"
                    >
                      <ArrowUpRight size={16} />
                    </a>
                  </div>
                </section>
                <section className="card preset-card">
                  <span className="small-icon">
                    <FlaskConical size={21} />
                  </span>
                  <h3>Ein guter Ausgangspunkt.</h3>
                  <p>
                    Die Parameter berücksichtigen die Textanzahl. Die
                    Themenqualität prüfst du anschließend an deinen Inhalten.
                  </p>
                  <button
                    className="text-button"
                    onClick={() =>
                      setParams(defaults(cleaned.defaults, namingModel))
                    }
                  >
                    <RotateCcw size={14} />
                    Voreinstellungen laden
                  </button>
                </section>
              </div>
              <div className="parameter-grid">
                <section className="card parameter-card">
                  <div className="card-title">
                    <Network size={18} />
                    <h3>UMAP</h3>
                    <span className="card-label">PROJEKTION</span>
                  </div>
                  <Range
                    label="Nachbarn"
                    value={params.umap.n_neighbors}
                    min={2}
                    max={100}
                    onChange={(n_neighbors) =>
                      change({ umap: { ...params.umap, n_neighbors } })
                    }
                    help="Kleine Werte betonen lokale Gruppen, größere Werte die globale Struktur. Muss unter der Textanzahl liegen."
                  />
                  <Range
                    label="Dimensionen"
                    value={params.umap.n_components}
                    min={2}
                    max={50}
                    onChange={(n_components) =>
                      change({ umap: { ...params.umap, n_components } })
                    }
                    help="Dimensionen für das Clustering, typischerweise 2 bis 5. Nicht die Achsen des Ergebnisdiagramms."
                  />
                  <Range
                    label="Minimale Distanz"
                    value={params.umap.min_dist}
                    min={0}
                    max={1}
                    step={0.01}
                    onChange={(min_dist) =>
                      change({ umap: { ...params.umap, min_dist } })
                    }
                    help="Kleine Werte ermöglichen dichtere Gruppen im reduzierten Raum."
                  />
                </section>
                <section className="card parameter-card">
                  <div className="card-title">
                    <CircleDot size={18} />
                    <h3>HDBSCAN</h3>
                    <span className="card-label">CLUSTERING</span>
                  </div>
                  <Range
                    label="Minimale Clustergröße"
                    value={params.hdbscan.min_cluster_size}
                    min={2}
                    max={100}
                    onChange={(min_cluster_size) =>
                      change({ hdbscan: { min_cluster_size } })
                    }
                    help="Wie viele Texte mindestens ein Thema bilden. Kleine Werte ergeben oft kleinere Themen."
                  />
                  <div className="card-divider" />
                  <div className="card-title compact">
                    <Type size={16} />
                    <h3>Themenbeschreibung</h3>
                  </div>
                  <Range
                    label="Keywords pro Thema"
                    value={params.top_n_words}
                    min={5}
                    max={30}
                    onChange={(top_n_words) => change({ top_n_words })}
                    help="Anzahl der beschreibenden Begriffe je Thema."
                  />
                  <div className="field-label">
                    Repräsentationen
                    <Help title="Repräsentationen">
                      KeyBERT wählt relevante Begriffe, MMR reduziert ähnliche
                      Wörter. Ohne Auswahl werden c-TF-IDF-Begriffe verwendet.
                    </Help>
                  </div>
                  <div className="chips">
                    {["KeyBERT", "MMR"].map((name) => (
                      <button
                        key={name}
                        className={
                          params.representation_models.includes(name)
                            ? "toggle-chip on"
                            : "toggle-chip"
                        }
                        aria-pressed={params.representation_models.includes(
                          name,
                        )}
                        onClick={() =>
                          change({
                            representation_models:
                              params.representation_models.includes(name)
                                ? params.representation_models.filter(
                                    (r) => r !== name,
                                  )
                                : [...params.representation_models, name],
                          })
                        }
                      >
                        {params.representation_models.includes(name) && (
                          <Check size={12} />
                        )}{" "}
                        {name}
                      </button>
                    ))}
                  </div>
                </section>
                <section className="card parameter-card">
                  <div className="card-title">
                    <Type size={18} />
                    <h3>Vektorisierung</h3>
                    <span className="card-label">BEGRIFFE</span>
                  </div>
                  <Field
                    label="N-Gramme"
                    help="Einzelwörter oder Wortfolgen, zum Beispiel „erneuerbare Energie“."
                  >
                    <Select
                      label="N-Gramme"
                      value={String(params.vectorizer.ngram_range[1])}
                      options={[
                        { value: "1", label: "Einzelwörter (1)" },
                        { value: "2", label: "Wörter & Wortpaare (1–2)" },
                        { value: "3", label: "Wörter & Phrasen (1–3)" },
                      ]}
                      onChange={(v) =>
                        change({
                          vectorizer: {
                            ...params.vectorizer,
                            ngram_range: [1, +v],
                          },
                        })
                      }
                    />
                  </Field>
                  <Range
                    label="Minimale Häufigkeit"
                    value={params.vectorizer.min_df}
                    min={0.0001}
                    max={1}
                    step={0.0001}
                    onChange={(min_df) =>
                      change({ vectorizer: { ...params.vectorizer, min_df } })
                    }
                    help="Mindestanteil zusammengefasster Themen, in denen ein Begriff vorkommen muss."
                  />
                  <Range
                    label="Maximale Häufigkeit"
                    value={params.vectorizer.max_df}
                    min={0.1}
                    max={1}
                    step={0.01}
                    onChange={(max_df) =>
                      change({ vectorizer: { ...params.vectorizer, max_df } })
                    }
                    help="Obergrenze der Themenhäufigkeit. Bei wenigen Themen ist 1,0 eine robuste Ausgangsbasis."
                  />
                </section>
              </div>
            </fieldset>
            <section className="card ai-card">
              <div className="ai-heading">
                <span className="ai-icon">
                  <Sparkles size={20} />
                </span>
                <div>
                  <h3>Verständliche Themennamen</h3>
                  <p>
                    Optional mit OpenAI, ausschließlich auf Basis der
                    Themen-Keywords.
                  </p>
                </div>
                <span
                  className={caps?.key_present ? "success-chip" : "quiet-chip"}
                >
                  {caps?.key_present ? "API-Key erkannt" : "Kein API-Key"}
                </span>
                <label className="switch">
                  <input
                    aria-label="Themen mit OpenAI benennen"
                    type="checkbox"
                    checked={params.name_topics}
                    disabled={!caps?.key_present || blocked}
                    onChange={(e) => change({ name_topics: e.target.checked })}
                  />
                  <span />
                </label>
              </div>
              <div className="ai-details">
                <span>
                  <ShieldCheck size={14} />
                  Keine Dokumenttexte. Keywords können vertrauliche Begriffe
                  enthalten.
                </span>
                <button
                  className="text-button"
                  onClick={() => setSettings(true)}
                >
                  <Link2 size={14} />
                  Verbindung & Modell
                </button>
              </div>
            </section>
            {invalid.length > 0 && (
              <div className="alert error" role="alert">
                {invalid.join(" ")}
              </div>
            )}
            <div className="action-bar">
              <button className="text-button" onClick={() => setStep(0)}>
                <ArrowLeft size={15} />
                Zurück zum Import
              </button>
              <div className="action-right">
                <span className="muted">
                  {cleaned.rows.toLocaleString("de-DE")} Texte · lokal auf
                  deinem Rechner
                </span>
                <button
                  className="button primary"
                  disabled={blocked || !!invalid.length}
                  onClick={() =>
                    void startJob("/train", {
                      params: { ...params, naming_model: namingModel },
                    })
                  }
                >
                  {active ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <Sparkles size={17} />
                  )}
                  Modell trainieren
                </button>
              </div>
            </div>
          </>
        )}
        {step === 2 && result && (
          <>
            <section className="section-heading">
              <div>
                <span className="section-kicker">03 / ERGEBNISSE</span>
                <h2>Deine Texte. Ihre Themen.</h2>
                <p>
                  Entdecke die Struktur deiner Daten und prüfe die Ergebnisse im
                  Zusammenhang.
                </p>
              </div>
              <button
                className="button secondary"
                disabled={blocked}
                onClick={() => void download()}
              >
                <Download size={16} />
                Ergebnisse exportieren
              </button>
            </section>
            <div className="result-stats">
              {[
                {
                  label: "Identifizierte Themen",
                  value: result.stats.topics,
                  icon: Layers3,
                },
                {
                  label: "Analysierte Texte",
                  value: result.stats.documents,
                  icon: FileSpreadsheet,
                },
                {
                  label: "Ausreißer",
                  value: `${result.stats.outliers} %`,
                  icon: CircleDot,
                },
                {
                  label: "Ø Texte pro Thema",
                  value: result.stats.average,
                  icon: ChartScatter,
                },
              ].map((stat) => (
                <div className="stat-card" key={stat.label}>
                  <span>{stat.label}</span>
                  <strong>
                    {stat.value}
                    <span className="stat-icon">
                      <stat.icon size={19} />
                    </span>
                  </strong>
                </div>
              ))}
            </div>
            <div className="results-toolbar">
              <div className="segmented">
                {[
                  { id: "topics", label: "Themenübersicht" },
                  { id: "documents", label: "Textbeiträge" },
                  { id: "charts", label: "Visualisierungen" },
                  { id: "parameters", label: "Parameter" },
                ].map((t) => (
                  <button
                    key={t.id}
                    className={resultTab === t.id ? "selected" : ""}
                    onClick={() => setResultTab(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
            {resultTab === "topics" && (
              <section className="card result-table">
                <div className="preview-heading">
                  <div>
                    <h3>Was deine Texte bewegt</h3>
                    <p>Thema −1 enthält Texte ohne stabile Clusterzuordnung.</p>
                  </div>
                  <span className="quiet-chip">
                    {result.stats.topics} Themen
                  </span>
                </div>
                <DataTable rows={topics} />
              </section>
            )}
            {resultTab === "documents" && (
              <section className="card result-table">
                <div className="table-tools">
                  <div className="search-input">
                    <Search size={16} />
                    <input
                      aria-label="Textbeiträge durchsuchen"
                      placeholder="Texte, IDs oder Themen durchsuchen …"
                      value={search}
                      onChange={(e) => {
                        setSearch(e.target.value);
                        setPage(0);
                      }}
                    />
                  </div>
                  <label className="inline-check">
                    <input
                      type="checkbox"
                      checked={grouped}
                      onChange={(e) => {
                        setGrouped(e.target.checked);
                        setPage(0);
                      }}
                    />
                    Nach ID gruppieren
                  </label>
                </div>
                {documents ? (
                  <>
                    <DataTable rows={documents.rows} />
                    <div className="pagination">
                      <span>
                        {documents.total} Einträge · {result.stats.unique_ids}{" "}
                        IDs
                      </span>
                      <div>
                        <button
                          className="icon-button"
                          disabled={!page}
                          aria-label="Vorherige Seite"
                          onClick={() => setPage((v) => v - 1)}
                        >
                          <ArrowLeft size={16} />
                        </button>
                        <span>Seite {page + 1}</span>
                        <button
                          className="icon-button"
                          disabled={(page + 1) * 50 >= documents.total}
                          aria-label="Nächste Seite"
                          onClick={() => setPage((v) => v + 1)}
                        >
                          <ArrowRight size={16} />
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="loading">
                    <LoaderCircle className="spin" />
                    Texte werden geladen …
                  </div>
                )}
              </section>
            )}
            {resultTab === "charts" && (
              <section className="card chart-card">
                <div className="chart-toolbar">
                  <div className="segmented small">
                    {[
                      { id: "similarity", label: "Themenähnlichkeit" },
                      { id: "bars", label: "Top-Keywords" },
                      { id: "network", label: "Dokumentenkarte" },
                    ].map((t) => (
                      <button
                        key={t.id}
                        className={chartKind === t.id ? "selected" : ""}
                        onClick={() => setChartKind(t.id)}
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>
                  {chartKind === "network" && (
                    <Select
                      label="Projektion"
                      value={method}
                      options={options(["umap", "tsne"])}
                      onChange={setMethod}
                    />
                  )}
                </div>
                <p className="chart-caption">
                  {chartKind === "similarity"
                    ? "Kosinus-Ähnlichkeit der häufigsten Themen. Kein statistischer z-Wert."
                    : chartKind === "bars"
                      ? "Repräsentationsgewichte – keine Wahrscheinlichkeiten. Wähle bis zu vier Themen."
                      : "Ein Punkt pro Text, Farben entsprechen Themen. Räumliche Nähe ist explorativ zu interpretieren."}
                </p>
                {chartKind === "bars" && (
                  <div className="chips topic-chips">
                    {topics
                      .filter((t) => t.Thema !== -1)
                      .map((t) => (
                        <button
                          key={t.Thema}
                          className={
                            selectedTopics.includes(t.Thema)
                              ? "toggle-chip on"
                              : "toggle-chip"
                          }
                          onClick={() =>
                            setSelectedTopics((old) =>
                              old.includes(t.Thema)
                                ? old.filter((id) => id !== t.Thema)
                                : old.length < 4
                                  ? [...old, t.Thema]
                                  : old,
                            )
                          }
                        >
                          {t.Thema} · {t.Bezeichnung}
                        </button>
                      ))}
                  </div>
                )}
                {chartError ? (
                  <p className="error-text">{chartError}</p>
                ) : chartKind === "bars" && !selectedTopics.length ? (
                  <div className="empty-inline">
                    Bitte mindestens ein Thema auswählen.
                  </div>
                ) : chart ? (
                  <Plot figure={chart} />
                ) : (
                  <div className="loading">
                    <LoaderCircle className="spin" />
                    Diagramm wird geladen …
                  </div>
                )}
              </section>
            )}
            {resultTab === "parameters" && (
              <section className="card">
                <h3>Verwendete Modellparameter</h3>
                <p className="muted">
                  Diese Werte gehören zum dargestellten Training.
                </p>
                <DataTable
                  rows={Object.entries(result.parameters).flatMap(
                    ([key, value]) =>
                      typeof value === "object" &&
                      value !== null &&
                      !Array.isArray(value)
                        ? Object.entries(value).map(([sub, v]) => ({
                            Parameter: `${key}.${sub}`,
                            Wert: JSON.stringify(v),
                          }))
                        : [{ Parameter: key, Wert: JSON.stringify(value) }],
                  )}
                />
              </section>
            )}
            <details className="card refine-card">
              <summary>
                <Settings2 size={17} />
                <strong>Ergebnisse verfeinern</strong>
                <span>Ausreißer & Themennamen</span>
              </summary>
              <div className="refine-grid">
                <div>
                  <h3>Ausreißer reduzieren</h3>
                  <p className="muted">
                    Änderungen aktualisieren Tabellen und Diagramme. Vorhandene
                    KI-Namen werden verworfen.
                  </p>
                  <Range
                    label="Schwellwert"
                    value={threshold}
                    min={0}
                    max={0.5}
                    step={0.01}
                    disabled={blocked}
                    onChange={setThreshold}
                    help="Kleine Werte ordnen mehr Ausreißer einem Thema zu."
                  />
                  <div className="button-row">
                    <button
                      className="button secondary"
                      disabled={blocked || !result.stats.outliers}
                      onClick={() => void startJob("/outliers", { threshold })}
                    >
                      Ausreißer zuordnen
                    </button>
                    <button
                      className="text-button"
                      disabled={blocked || !result.can_restore}
                      onClick={() => void startJob("/outliers/restore")}
                    >
                      <RotateCcw size={14} />
                      Zurücksetzen
                    </button>
                  </div>
                </div>
                <div>
                  <h3>Themen mit OpenAI benennen</h3>
                  <p className="muted">
                    Nur die gezeigten Keywords werden übertragen – keine
                    Dokumenttexte. API-Nutzung kostet zusätzlich.
                  </p>
                  <div className="keyword-preview">
                    {keywords.map((t) => (
                      <p key={t.id}>
                        <strong>{t.id}</strong>
                        {t.keywords.join(", ")}
                      </p>
                    ))}
                  </div>
                  <button
                    className="button secondary"
                    disabled={blocked || !caps?.key_present || !keywords.length}
                    onClick={() =>
                      void startJob("/name", { model: namingModel })
                    }
                  >
                    <Sparkles size={15} />
                    Keywords senden & benennen
                  </button>
                  {!caps?.key_present && (
                    <button
                      className="text-button"
                      onClick={() => setSettings(true)}
                    >
                      API-Key einrichten
                      <ArrowUpRight size={14} />
                    </button>
                  )}
                </div>
              </div>
            </details>
          </>
        )}
        <footer>
          <span>
            <Layers3 size={13} />
            themncluster
          </span>
          <span>#NDRfragt Topic Modeling</span>
        </footer>
      </main>
      {settings && (
        <div className="modal-backdrop" onClick={() => setSettings(false)}>
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="OpenAI-Verbindung"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-heading">
              <span className="small-icon">
                <Link2 size={21} />
              </span>
              <h2>OpenAI-Verbindung</h2>
              <button
                autoFocus
                className="icon-button"
                aria-label="Dialog schließen"
                onClick={() => setSettings(false)}
              >
                <X size={20} />
              </button>
            </div>
            <p className="muted">
              Optional für Themennamen. Das lokale Training funktioniert ohne
              API-Key.
            </p>
            <div
              className={caps?.key_present ? "alert notice" : "alert neutral"}
            >
              <ShieldCheck size={17} />
              <span>
                {caps?.key_present
                  ? `API-Key erkannt · ${caps.key_source}`
                  : "Kein API-Key hinterlegt"}
              </span>
            </div>
            <Field label="Modell für Themennamen">
              <Select
                label="OpenAI-Modell"
                value={namingModel}
                options={Object.entries(caps?.naming_models || {}).map(
                  ([value, label]) => ({ value, label: String(label) }),
                )}
                disabled={!caps?.key_present}
                onChange={setNamingModel}
              />
            </Field>
            <button
              className="button secondary"
              disabled={!caps?.key_present || !!busy}
              onClick={() =>
                void perform("api", async () => {
                  const value = await api(
                    "/openai/check",
                    token,
                    post({ model: namingModel }),
                  );
                  setNotice(value.message);
                  setSettings(false);
                })
              }
            >
              <Link2 size={15} />
              API-Zugriff prüfen
            </button>
            <div className="setup-note">
              <h3>Key lokal hinterlegen</h3>
              <p>
                In <code>.streamlit/secrets.toml</code> im Projektverzeichnis:
              </p>
              <pre>OPENAI_API_KEY = "DEIN_NEUER_API_KEY"</pre>
              <p>
                Alternativ als Umgebungsvariable. Der Key bleibt auf dem
                Python-Server. Nach Änderungen den Server neu starten.
              </p>
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noreferrer"
              >
                OpenAI API keys
                <ArrowUpRight size={13} />
              </a>
            </div>
            <p className="fineprint">
              ChatGPT Pro beinhaltet keine API-Nutzung. Die Verbindungskontrolle
              prüft die Modellsichtbarkeit, nicht Guthaben oder
              Responses-Berechtigung.
            </p>
            {error && (
              <p role="alert" className="error-text">
                {error}
              </p>
            )}
          </section>
        </div>
      )}
    </>
  );
}
