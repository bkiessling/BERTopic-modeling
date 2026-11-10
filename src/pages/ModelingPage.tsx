import helpText from "../content/help.de.json";
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
    requestNaming,
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
              <Help title="Voreinstellungen">{helpText.presets}</Help>
            </div>
            <p>
              Ausgangswerte für {cleaned.rows.toLocaleString("de-DE")} Texte.
            </p>
            <button
              className="button secondary preset-reset"
              onClick={() => setParams(defaults(cleaned.defaults, namingModel))}
            >
              Parameter zurücksetzen
            </button>
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
              <Help title="Embeddings">{helpText.embeddings}</Help>
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
                  disabled={blocked}
                  onChange={(e) => requestNaming(e.target.checked)}
                />
                <span />
              </label>
            </div>
            <div className="ai-details">
              <button
                className="button secondary"
                onClick={() => setSettings(true)}
              >
                OpenAI-Modell
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
              help={helpText.neighbors}
            />
            <Range
              label="Dimensionen"
              value={params.umap.n_components}
              min={2}
              max={50}
              onChange={(n_components) =>
                change({ umap: { ...params.umap, n_components } })
              }
              help={helpText.dimensions}
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
              help={helpText.distance}
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
              help={helpText.clusterSize}
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
              help={helpText.topicWords}
            />
            <div className="field-label">
              Repräsentationen
              <Help title="Repräsentationen">{helpText.representations}</Help>
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
            <Field label="N-Gramme" help={helpText.ngrams}>
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
              help={helpText.minFrequency}
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
              help={helpText.maxFrequency}
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
