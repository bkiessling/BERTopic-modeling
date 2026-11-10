import { useWorkbench } from "../context/WorkbenchContext";
import type { Row } from "../api";
import { defaults } from "../api";
import {
  ArrowLeft,
  ArrowUpRight,
  Check,
  FileSpreadsheet,
  FlaskConical,
  Layers3,
  ShieldCheck,
  Sparkles,
  Network,
  Type,
  RotateCcw,
  CircleDot,
  Link2,
} from "lucide-react";
import { Field, Help, Range, Select } from "../components";
export function ModelingPage() {
  const {
    caps,
    step,
    setStep,
    cleaned,
    params,
    setParams,
    error,
    setSettings,
    namingModel,
    active,
    blocked,
    change,
    startJob,
    modelOptions,
    invalid,
    options,
  } = useWorkbench();
  if (!params || !cleaned) return null;
  return (
    <>
      <section className="section-heading">
        <div>
          <h2>Modellierung</h2>
          <p>Parameter für die Themenmodellierung.</p>
        </div>
        <span className="quiet-chip">
          <FileSpreadsheet size={14} />
          {cleaned.rows.toLocaleString("de-DE")} Texte
        </span>
      </section>
      <fieldset className="model-fieldset" disabled={blocked}>
        <div className="model-top-grid">
          <section className="card preset-card">
            <div className="preset-heading">
              <h3>Voreinstellungen</h3>
              <button
                className="icon-button reset-control"
                aria-label="Parameter zurücksetzen"
                title="Voreinstellungen wiederherstellen"
                onClick={() =>
                  setParams(defaults(cleaned.defaults, namingModel))
                }
              >
                <RotateCcw size={18} />
              </button>
            </div>
            <p>
              Ausgangswerte für {cleaned.rows.toLocaleString("de-DE")} Texte.
            </p>
            <div className="preset-training">
              <h3>Training</h3>
              <p>Mit den gewählten Parametern starten.</p>
              <button
                className="button primary"
                disabled={blocked || !!invalid.length}
                onClick={() =>
                  void startJob("/train", {
                    params: { ...params, naming_model: namingModel },
                  })
                }
              >
                {active ? "Training läuft …" : "Modell trainieren"}
              </button>
            </div>
          </section>
          <section className="card">
            <div className="card-title">
              <Layers3 size={18} />
              <h3>Sprache & Embeddings</h3>
              <Help title="Embeddings">
                Das Sprachmodell übersetzt Texte in Bedeutungsvektoren. Deutsche
                Texte brauchen ein deutschfähiges Modell.
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
                  onChange={(embedding_model) => change({ embedding_model })}
                />
              </Field>
            </div>
            <div className="model-note">
              <span className="dot violet" />
              <p>
                {
                  modelOptions.find((m) => m.id === params.embedding_model)
                    ?.description
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

          <section className="card ai-card">
            <div className="ai-heading">
              <span className="ai-icon">
                <Type size={20} />
              </span>
              <div>
                <h3>Themen automatisch benennen</h3>
                <p>Optional mit OpenAI aus den Themen-Keywords.</p>
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
              <button
                className="button secondary"
                onClick={() => setSettings(true)}
              >
                Verbindung & Modell
              </button>
            </div>
          </section>
        </div>
        <div className="parameter-grid">
          <section className="card parameter-card">
            <div className="card-title">
              <Network size={18} />
              <h3>UMAP</h3>
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
                KeyBERT wählt relevante Begriffe, MMR reduziert ähnliche Wörter.
                Ohne Auswahl werden c-TF-IDF-Begriffe verwendet.
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
                  aria-pressed={params.representation_models.includes(name)}
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
            {cleaned.rows.toLocaleString("de-DE")} Texte · lokal auf deinem
            Rechner
          </span>
        </div>
      </div>
    </>
  );
}
