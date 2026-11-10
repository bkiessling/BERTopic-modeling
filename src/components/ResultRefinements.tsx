import { useEffect, useState } from "react";
import { Settings2 } from "lucide-react";
import { useWorkbench } from "../context/WorkbenchContext";
import { Field, Help, MultiSelect, Range, Select } from "./index";
import type { Row } from "../api";
import helpText from "../content/help.de.json";

export function ResultRefinements() {
  const {
    result,
    topics,
    caps,
    blocked,
    threshold,
    setThreshold,
    namingModel,
    setSettings,
    keywords,
    startJob,
    renameTopic,
  } = useWorkbench();
  const [targetTopics, setTargetTopics] = useState(2);
  const [mergeTopics, setMergeTopics] = useState<number[]>([]);
  const [editTopic, setEditTopic] = useState("");
  const [label, setLabel] = useState("");
  useEffect(() => {
    setMergeTopics([]);
  }, [result]);
  useEffect(() => {
    const topic = topics.find((topic) => String(topic.Thema) === editTopic);
    if (!topic) {
      setEditTopic("");
      setLabel("");
    } else setLabel(topic.Themenname);
  }, [result, editTopic]);
  if (!result) return null;
  const available = topics.filter((topic) => topic.Thema !== -1);
  const topicLabel = (topic: Row) => `${topic.Thema} · ${topic.Themenname}`;
  return (
    <>
      <details className="card refine-card">
        <summary>
          <Settings2 size={17} />
          <strong>Ergebnisse verbessern</strong>
          <span>Outlier, Themen & Namen</span>
        </summary>
        <div className="refine-grid">
          <div>
            <div className="card-title compact">
              <h3>Outlier reduzieren</h3>
              <Help title="Outlier reduzieren">
                {helpText.outlierExplanation}
              </Help>
            </div>
            <p className="muted">
              Änderungen aktualisieren Tabellen und Diagramme. Vorhandene
              manuelle und KI-Namen werden verworfen.
            </p>
            <Range
              label="Schwellwert"
              value={threshold}
              min={0}
              max={0.5}
              step={0.01}
              disabled={blocked}
              onChange={setThreshold}
              help={helpText.outliers}
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
            <div className="card-title compact">
              <h3>Themen reduzieren</h3>
              <Help title="Themen reduzieren">{helpText.topicReduction}</Help>
            </div>
            <p className="muted">
              Ähnliche Themen auf eine Zielanzahl zusammenfassen. Outlier werden
              nicht mitgezählt.
            </p>
            <Field label="Zielanzahl Themen">
              <input
                type="number"
                aria-label="Zielanzahl Themen"
                min={1}
                max={Math.max(1, result.stats.topics - 1)}
                value={Math.min(
                  targetTopics,
                  Math.max(1, result.stats.topics - 1),
                )}
                disabled={blocked || result.stats.topics < 2}
                onChange={(event) =>
                  setTargetTopics(Number(event.target.value))
                }
              />
            </Field>
            <button
              className="button secondary"
              disabled={
                blocked ||
                result.stats.topics < 2 ||
                !Number.isInteger(targetTopics) ||
                targetTopics < 1
              }
              onClick={() =>
                void startJob("/topics/reduce", {
                  target: Math.min(targetTopics, result.stats.topics - 1),
                })
              }
            >
              Themen zusammenfassen
            </button>
            <p className="muted">
              Themennamen und die bisherige Outlier-Zurücksetzung werden dabei
              verworfen.
            </p>
          </div>
          <div>
            <div className="card-title compact">
              <h3>Themen gezielt zusammenführen</h3>
              <Help title="Themen zusammenführen">{helpText.topicMerge}</Help>
            </div>
            <p className="muted">
              Mindestens zwei Themen auswählen, die eine gemeinsame Gruppe
              bilden sollen.
            </p>
            <Field label="Themen zum Zusammenführen">
              <MultiSelect
                label="Themen zum Zusammenführen"
                itemLabel="Thema"
                placeholder="Themen auswählen"
                options={available.map(topicLabel)}
                values={available
                  .filter((topic) => mergeTopics.includes(topic.Thema))
                  .map(topicLabel)}
                onChange={(values) =>
                  setMergeTopics(
                    values.map((value) => Number(value.split(" · ")[0])),
                  )
                }
                disabled={blocked}
              />
            </Field>
            <button
              className="button secondary"
              disabled={blocked || mergeTopics.length < 2}
              onClick={() =>
                void startJob("/topics/merge", { topics: mergeTopics })
              }
            >
              Ausgewählte Themen zusammenführen
            </button>
            <p className="muted">
              Andere Themen behalten ihre Namen. Die neue Gruppe erhält zunächst
              Keywords als Namen; die bisherige Outlier-Zurücksetzung entfällt.
            </p>
          </div>
          <div>
            <div className="card-title compact">
              <h3>Themennamen bearbeiten</h3>
              <Help title="Themennamen bearbeiten">
                {helpText.manualTopicName}
              </Help>
            </div>
            <p className="muted">
              Ein Thema wählen und den Namen direkt ändern. Outlier behalten
              ihren festen Namen.
            </p>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                if (editTopic !== "" && label.trim())
                  void renameTopic(Number(editTopic), label.trim());
              }}
            >
              <Field label="Thema umbenennen">
                <Select
                  label="Thema umbenennen"
                  value={editTopic}
                  onChange={setEditTopic}
                  options={[
                    { value: "", label: "Thema auswählen" },
                    ...available.map((topic) => ({
                      value: String(topic.Thema),
                      label: topicLabel(topic),
                    })),
                  ]}
                  disabled={blocked}
                />
              </Field>
              <Field label="Neuer Themenname">
                <input
                  aria-label="Neuer Themenname"
                  type="text"
                  value={label}
                  maxLength={120}
                  onChange={(event) => setLabel(event.target.value)}
                  disabled={blocked || editTopic === ""}
                />
              </Field>
              <button
                className="button secondary"
                disabled={
                  blocked ||
                  editTopic === "" ||
                  !label.trim() ||
                  available.find((topic) => String(topic.Thema) === editTopic)
                    ?.Themenname === label.trim()
                }
              >
                Themenname speichern
              </button>
            </form>
          </div>
        </div>
        <div className="rename-section">
          <div>
            <h3>Themen neu benennen</h3>
            <p className="muted">
              Nach Strukturänderungen Namen mit KI neu vergeben. Manuell
              bearbeitete Namen bleiben bei dieser Benennung erhalten.
            </p>
            {result.naming_needs_refresh && (
              <p className="naming-refresh">
                Die Themenstruktur wurde geändert. Bitte Themen neu benennen.
              </p>
            )}
          </div>
          <button
            className="button secondary"
            disabled={blocked || !keywords.length}
            onClick={() =>
              caps?.key_present
                ? void startJob("/name", { model: namingModel })
                : setSettings(true)
            }
          >
            Themen neu benennen
          </button>
        </div>
      </details>
    </>
  );
}
