import { useWorkbench } from "../../state/WorkbenchContext";
import type { Row } from "../../api";
import {
  ArrowRight,
  ArrowLeft,
  ArrowUpRight,
  FileSpreadsheet,
  Layers3,
  LoaderCircle,
  Search,
  Settings2,
  ChartScatter,
  RotateCcw,
  CircleDot,
} from "lucide-react";
import { DataTable, Plot, Range, Select } from "../../components";
export function ResultsView() {
  const {
    caps,
    step,
    result,
    error,
    resultTab,
    setResultTab,
    setStep,
    chartKind,
    setChartKind,
    chart,
    chartError,
    selectedTopics,
    setSelectedTopics,
    method,
    setMethod,
    documents,
    search,
    setSearch,
    page,
    setPage,
    grouped,
    setGrouped,
    threshold,
    setThreshold,
    setSettings,
    namingModel,
    blocked,
    startJob,
    download,
    topics,
    keywords,
    options,
  } = useWorkbench();
  if (!result) return null;
  return (
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
            <span className="quiet-chip">{result.stats.topics} Themen</span>
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
                  {documents.total} Einträge · {result.stats.unique_ids} IDs
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
            rows={Object.entries(result.parameters).flatMap(([key, value]) =>
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
                className="button secondary"
                disabled={blocked || !result.can_restore}
                onClick={() => void startJob("/outliers/restore")}
              >
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
              onClick={() => void startJob("/name", { model: namingModel })}
            >
              Keywords senden & benennen
            </button>
            {!caps?.key_present && (
              <button
                className="button secondary"
                onClick={() => setSettings(true)}
              >
                API-Key einrichten
              </button>
            )}
          </div>
        </div>
      </details>
      <div className="action-bar">
        <button className="text-button" onClick={() => setStep(1)}>
          Zur Modellierung
        </button>{" "}
        <button
          className="button primary"
          disabled={blocked}
          onClick={() => void download()}
        >
          Ergebnisse exportieren
        </button>
      </div>
    </>
  );
}
