import { Check, LoaderCircle } from "lucide-react";
import type { Job } from "../api";

export function TrainingProgress({
  job,
  namingEnabled,
}: {
  job: Job;
  namingEnabled: boolean;
}) {
  const running = job.status === "running" || job.status === "queued";
  const stages = [
    { label: "Modell laden", start: 0, end: 5 },
    { label: "Embeddings", start: 5, end: 20 },
    { label: "UMAP, HDBSCAN & Begriffe konfigurieren", start: 20, end: 60 },
    { label: "Modell fitten", start: 60, end: namingEnabled ? 92 : 95 },
    ...(namingEnabled
      ? [{ label: "Themen benennen", start: 92, end: 95 }]
      : []),
    { label: "Visualisierungen", start: 95, end: 100 },
  ];
  return (
    <section
      className="job-card"
      aria-live="polite"
      aria-label="Trainingsstatus"
    >
      <div className="job-title">
        {running && <LoaderCircle size={16} className="spin" />}
        <strong>{job.message}</strong>
        <span>{job.progress}%</span>
      </div>
      <progress
        aria-label="Modellierungsfortschritt"
        max={100}
        value={job.progress}
      />
      {job.kind === "training" && (
        <ol className="training-stages">
          {stages.map((stage) => {
            const complete = job.progress >= stage.end;
            const active =
              running &&
              job.progress >= stage.start &&
              job.progress < stage.end;
            return (
              <li
                key={stage.label}
                className={complete ? "done" : active ? "current" : ""}
                aria-current={active ? "step" : undefined}
              >
                <span className="stage-marker">
                  {complete ? <Check size={11} /> : null}
                </span>
                {stage.label}
              </li>
            );
          })}
        </ol>
      )}
      {job.error && <p className="error-text">{job.error}</p>}
      <p className="muted">
        {running
          ? "Fortschritt nach Arbeitsschritten, keine Zeitprognose."
          : "Bisherige Ergebnisse bleiben erhalten."}
      </p>
    </section>
  );
}
