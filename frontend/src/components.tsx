import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { HelpCircle, X, ChevronDown } from "lucide-react";
import type { Row } from "./api";
export function Help({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <span className="help">
      <button
        type="button"
        className="icon-button"
        aria-label={`Hilfe zu ${title}`}
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <HelpCircle size={15} />
      </button>
      {open && (
        <span className="help-popover" role="note">
          <strong>{title}</strong>
          {children}
          <button
            aria-label="Hilfe schließen"
            className="help-close"
            onClick={() => setOpen(false)}
          >
            <X size={13} />
          </button>
        </span>
      )}
    </span>
  );
}
export function Field({
  label,
  help,
  children,
}: {
  label: string;
  help?: string;
  children: ReactNode;
}) {
  return (
    <div className="field">
      <div className="field-label">
        <span>{label}</span>
        {help && <Help title={label}>{help}</Help>}
      </div>
      {children}
    </div>
  );
}
export function Select({
  label,
  value,
  options,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="select-wrap">
      <select
        aria-label={label}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown size={16} />
    </div>
  );
}
export function Range({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  help,
  disabled = false,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
  help: string;
  disabled?: boolean;
}) {
  return (
    <div className="range-field">
      <div className="field-label">
        <span>
          {label}
          <Help title={label}>{help}</Help>
        </span>
        <output>
          {value.toLocaleString("de-DE", { maximumFractionDigits: 4 })}
        </output>
      </div>
      <input
        type="range"
        aria-label={label}
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(+e.target.value)}
      />
      <div className="range-bounds">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
export function DataTable({ rows }: { rows: Row[] }) {
  if (!rows.length)
    return <div className="empty-inline">Keine Einträge vorhanden.</div>;
  const cols = Object.keys(rows[0]);
  const display = (v: any) =>
    v == null
      ? "—"
      : Array.isArray(v)
        ? v.join(", ")
        : typeof v === "object"
          ? JSON.stringify(v)
          : String(v);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c} title={display(r[c])}>
                  {display(r[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function Plot({ figure }: { figure: any }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let disposed = false;
    let engine: any;
    const target = ref.current;
    import("plotly.js-dist-min")
      .then(async (m) => {
        engine = m.default;
        if (disposed || !target) return;
        await engine.newPlot(
          target,
          figure.data,
          { ...figure.layout, autosize: true, width: undefined },
          {
            responsive: true,
            displaylogo: false,
            toImageButtonOptions: { format: "png", scale: 2 },
          },
        );
        if (disposed) engine.purge(target);
      })
      .catch(() => {
        if (!disposed) setError("Diagramm konnte nicht geladen werden.");
      });
    return () => {
      disposed = true;
      if (engine && target) engine.purge(target);
    };
  }, [figure]);
  return error ? (
    <p className="error-text">{error}</p>
  ) : (
    <div
      className="plot"
      ref={ref}
      aria-label="Interaktives Ergebnisdiagramm"
    />
  );
}

export function MultiSelect({
  label,
  values,
  options,
  onChange,
  disabled = false,
}: {
  label: string;
  values: string[];
  options: string[];
  onChange: (values: string[]) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);
  return (
    <div
      className="multiselect"
      ref={root}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setOpen(false);
          trigger.current?.focus();
        }
      }}
    >
      <button
        type="button"
        ref={trigger}
        className="multiselect-trigger"
        aria-label={label}
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen(!open)}
      >
        <span>
          {values.length ? values.join(", ") : "Textspalten auswählen"}
        </span>
        <span className="selection-count">{values.length}</span>
        <ChevronDown size={16} />
      </button>
      {open && !disabled && (
        <div
          className="multiselect-panel"
          role="group"
          aria-label={`${label} auswählen`}
        >
          {options.map((option) => (
            <label className="multiselect-option" key={option}>
              <input
                type="checkbox"
                aria-label={`Textspalte ${option}`}
                checked={values.includes(option)}
                onChange={() =>
                  onChange(
                    values.includes(option)
                      ? values.filter((value) => value !== option)
                      : [...values, option],
                  )
                }
              />
              <span>{option}</span>
            </label>
          ))}
          {!options.length && (
            <span className="muted">Keine Textspalten vorhanden.</span>
          )}
        </div>
      )}
    </div>
  );
}
