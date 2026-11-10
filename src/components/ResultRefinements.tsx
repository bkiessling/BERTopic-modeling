import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Settings2 } from "lucide-react";
import { useWorkbench } from "../context/WorkbenchContext";
import { Field, Help, MultiSelect, Range, Select } from "./index";
import type { Row } from "../api";
import helpText from "../content/help.de.json";

function Refinement({
  title,
  help,
  children,
  actions,
}: {
  title: string;
  help?: string;
  children: ReactNode;
  actions: ReactNode;
}) {
  return (
    <section className="refine-item">
      <div className="card-title compact">
        <h3>{title}</h3>
        {help && <Help title={title}>{help}</Help>}
      </div>
      <div className="refine-body">{children}</div>
      <div className="refine-actions">{actions}</div>
    </section>
  );
}

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
    updateExclusions,
  } = useWorkbench();
  const [targetTopics, setTargetTopics] = useState(2);
  const [mergeTopics, setMergeTopics] = useState<number[]>([]);
  const [excludeTopics, setExcludeTopics] = useState<number[]>([]);
  const [editTopic, setEditTopic] = useState("");
  const [label, setLabel] = useState("");
  useEffect(() => {
    setMergeTopics([]);
    setExcludeTopics([]);
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
  const excluded = result.excluded_topics || [];
  const structureBlocked = blocked || excluded.length > 0;
  return (
    <details className="card refine-card">
      <summary>
        <Settings2 size={17} />
        <strong>Ergebnisse verbessern</strong>
        <span>Outlier, Themen & Namen</span>
      </summary>
      {!!excluded.length && (
        <p className="refine-note">
          {excluded.length} Themen ausgeschlossen. Vor Strukturänderungen bitte
          alle Themen wieder einblenden.
        </p>
      )}
      <div className="refine-grid">
        <Refinement
          title="Outlier reduzieren"
          help={helpText.outlierExplanation}
          actions={
            <>
              <button
                className="button secondary"
                disabled={structureBlocked || !result.stats.outliers}
                onClick={() => void startJob("/outliers", { threshold })}
              >
                Outlier zuordnen
              </button>
              <button
                className="button secondary"
                disabled={structureBlocked || !result.can_restore}
                onClick={() => void startJob("/outliers/restore")}
              >
                Zurücksetzen
              </button>
            </>
          }
        >
          <p className="muted">
            Passende Outlier bestehenden Themen zuordnen. Manuelle und KI-Namen
            werden dabei verworfen.
          </p>
          <Range
            label="Schwellwert"
            value={threshold}
            min={0}
            max={0.5}
            step={0.01}
            disabled={structureBlocked}
            onChange={setThreshold}
            help={helpText.outliers}
          />
        </Refinement>
        <Refinement
          title="Themen reduzieren"
          help={helpText.topicReduction}
          actions={
            <button
              className="button secondary"
              disabled={
                structureBlocked ||
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
          }
        >
          <p className="muted">
            Ähnliche Themen automatisch auf eine Zielanzahl zusammenfassen.
            Outlier werden nicht mitgezählt.
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
              disabled={structureBlocked || result.stats.topics < 2}
              onChange={(event) => setTargetTopics(Number(event.target.value))}
            />
          </Field>
          <p className="muted">
            Themennamen und die bisherige Outlier-Zurücksetzung entfallen.
          </p>
        </Refinement>
        <Refinement
          title="Themen gezielt zusammenführen"
          help={helpText.topicMerge}
          actions={
            <button
              className="button secondary"
              disabled={structureBlocked || mergeTopics.length < 2}
              onClick={() =>
                void startJob("/topics/merge", { topics: mergeTopics })
              }
            >
              Ausgewählte Themen zusammenführen
            </button>
          }
        >
          <p className="muted">
            Mindestens zwei Themen auswählen, die eine gemeinsame Gruppe bilden
            sollen.
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
              disabled={structureBlocked}
              onChange={(values) =>
                setMergeTopics(
                  values.map((value) => Number(value.split(" · ")[0])),
                )
              }
            />
          </Field>
          <p className="muted">
            Andere Namen bleiben erhalten. Die neue Gruppe erhält zunächst
            Keywords als Namen; die bisherige Outlier-Zurücksetzung entfällt.
          </p>
        </Refinement>
        <Refinement
          title="Themennamen bearbeiten"
          help={helpText.manualTopicName}
          actions={
            <button
              className="button secondary"
              form="topic-name-form"
              type="submit"
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
          }
        >
          <p className="muted">
            Ein Thema wählen und den Namen direkt ändern. Outlier behalten ihren
            festen Namen.
          </p>
          <form
            id="topic-name-form"
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
                disabled={blocked}
                options={[
                  { value: "", label: "Thema auswählen" },
                  ...available.map((topic) => ({
                    value: String(topic.Thema),
                    label: topicLabel(topic),
                  })),
                ]}
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
          </form>
        </Refinement>
        <Refinement
          title="Themen neu benennen"
          actions={
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
          }
        >
          <p className="muted">
            Namen mit KI neu vergeben. Manuell bearbeitete Namen bleiben
            erhalten.
          </p>
          {result.naming_needs_refresh && (
            <p className="naming-refresh">
              Die Themenstruktur wurde geändert. Bitte Themen neu benennen.
            </p>
          )}
        </Refinement>
        <Refinement
          title="Themen ausschließen"
          help={helpText.topicExclusion}
          actions={
            <>
              <button
                className="button secondary"
                disabled={
                  blocked ||
                  !excludeTopics.length ||
                  excludeTopics.length >= topics.length
                }
                onClick={() => void updateExclusions(excludeTopics)}
              >
                Themen ausschließen
              </button>
              <button
                className="button secondary"
                disabled={blocked || !excluded.length}
                onClick={() => void updateExclusions()}
              >
                Alle wieder einblenden
              </button>
            </>
          }
        >
          <p className="muted">
            Themen aus Tabellen, Kennzahlen, Visualisierungen und Export
            ausblenden. Texte werden nicht gelöscht.
          </p>
          <Field label="Themen zum Ausschließen">
            <MultiSelect
              label="Themen zum Ausschließen"
              itemLabel="Thema"
              placeholder="Themen auswählen"
              options={topics.map(topicLabel)}
              values={topics
                .filter((topic) => excludeTopics.includes(topic.Thema))
                .map(topicLabel)}
              disabled={blocked}
              onChange={(values) =>
                setExcludeTopics(
                  values.map((value) => Number(value.split(" · ")[0])),
                )
              }
            />
          </Field>
          {!!excluded.length && (
            <p className="muted">
              Ausgeschlossen:{" "}
              {excluded
                .map((topic: Row) => `${topic.Topic} · ${topic.CustomName}`)
                .join(", ")}
            </p>
          )}
        </Refinement>
      </div>
    </details>
  );
}
