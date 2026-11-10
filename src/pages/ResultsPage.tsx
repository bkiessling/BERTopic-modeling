import { useState } from "react";
import { Plot } from "../charts/Plot";
import { useWorkbench } from "../context/WorkbenchContext";
import type { Row } from "../api";
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
import { DataTable, Range, Select, MultiSelect, Field } from "../components";
export function ResultsPage() {
  const [showParameters, setShowParameters] = useState(false);
  const {
    caps,
    topWords,
    setTopWords,
    documentTopic,
    setDocumentTopic,
    documentSort,
    setDocumentSort,
    descending,
    setDescending,
    representative,
    setRepresentative,
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
          <h2>Ergebnisse</h2>
          <p>Themen, Textbeiträge und Visualisierungen.</p>
        </div>
        <button
          className="icon-button"
          aria-label="Modellparameter anzeigen"
          aria-expanded={showParameters}
          onClick={() => setShowParameters((value) => !value)}
        >
          <Settings2 size={18} />
        </button>
      </section>
      {showParameters && (
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
            label: "Outlier",
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
            { id: "charts", label: "Visualisierungen" },
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
      <details className="card refine-card">
        <summary>
          <Settings2 size={17} />
          <strong>Ergebnisse verbessern</strong>
          <span>Outlier & Themennamen</span>
        </summary>
        <div className="refine-grid">
          <div>
            <h3>Outlier reduzieren</h3>
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
              help="Kleine Werte ordnen mehr Outlier einem Thema zu."
            />
            <div className="button-row">
              <button
                className="button secondary"
                disabled={blocked || !result.stats.outliers}
                onClick={() => void startJob("/outliers", { threshold })}
              >
                Outlier zuordnen
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
      {resultTab === "topics" && (
        <section className="card result-table">
          <div className="preview-heading">
            <div>
              <h3>Themenübersicht</h3>
              <p>Thema −1 enthält Texte ohne stabile Clusterzuordnung.</p>
            </div>
            <span className="quiet-chip">{result.stats.topics} Themen</span>
          </div>
          <DataTable rows={topics} />
        </section>
      )}
      {resultTab === "charts" && (
        <section
          className={`card chart-card ${chartKind === "network" ? "network-card" : ""}`}
        >
          <div className="chart-toolbar">
            <div className="segmented small">
              {[
                { id: "network", label: "Netzwerk" },
                { id: "similarity", label: "Themenähnlichkeit" },
                { id: "bars", label: "Top-Keywords" },
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
            <div className="keyword-controls">
              <Field label="Themen auswählen (max. 4)">
                <MultiSelect
                  label="Themen für Top-Keywords"
                  itemLabel="Thema"
                  placeholder="Themen auswählen"
                  maxSelections={4}
                  options={topics
                    .filter((t) => t.Thema !== -1)
                    .map((t) => `${t.Thema} · ${t.Bezeichnung}`)}
                  values={topics
                    .filter((t) => selectedTopics.includes(t.Thema))
                    .map((t) => `${t.Thema} · ${t.Bezeichnung}`)}
                  onChange={(values) =>
                    setSelectedTopics(
                      values.map((value) => Number(value.split(" · ")[0])),
                    )
                  }
                />
              </Field>
              <Range
                label="Anzahl Keywords"
                help="Zeigt die wichtigsten gespeicherten Keywords je Thema. Die Obergrenze entspricht den Keywords des trainierten Modells."
                value={topWords}
                min={1}
                max={Math.max(1, Math.min(30, result.parameters.top_n_words))}
                step={1}
                onChange={setTopWords}
              />
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
      {result && (
        <section className="card result-table documents-card">
          <div className="preview-heading">
            <div>
              <h3>Textbeiträge</h3>
              <p>
                Nach Thema filtern und über die Spaltenüberschriften sortieren.
              </p>
            </div>
          </div>
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
            <Select
              label="Nach Thema filtern"
              value={documentTopic}
              onChange={(value) => {
                setDocumentTopic(value);
                setPage(0);
              }}
              options={[
                { value: "", label: "Alle Themen" },
                ...topics.map((t) => ({
                  value: String(t.Thema),
                  label: `${t.Thema} · ${t.Bezeichnung}`,
                })),
              ]}
            />
            <label className="inline-check">
              <input
                type="checkbox"
                checked={representative}
                onChange={(e) => {
                  setRepresentative(e.target.checked);
                  setPage(0);
                }}
              />
              Nur repräsentative Beiträge
            </label>
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
              <DataTable
                rows={documents.rows}
                sort={documentSort}
                descending={descending}
                onSort={(column) => {
                  if (documentSort === column) setDescending(!descending);
                  else {
                    setDocumentSort(column);
                    setDescending(false);
                  }
                  setPage(0);
                }}
              />
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
