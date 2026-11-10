import { useState, useEffect, useRef } from "react";
import { ChevronDown } from "lucide-react";
export function MultiSelect({
  label,
  values,
  options,
  onChange,
  disabled = false,
  itemLabel = "Textspalte",
  placeholder = "Textspalten auswählen",
  maxSelections,
}: {
  label: string;
  values: string[];
  options: string[];
  onChange: (values: string[]) => void;
  disabled?: boolean;
  itemLabel?: string;
  placeholder?: string;
  maxSelections?: number;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const matches = options.filter((option) =>
    option
      .toLocaleLowerCase("de")
      .includes(query.trim().toLocaleLowerCase("de")),
  );
  useEffect(() => {
    if (!open) return;
    search.current?.focus();
    const outside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);
  function toggle(value: string) {
    if (
      !values.includes(value) &&
      maxSelections &&
      values.length >= maxSelections
    )
      return;
    onChange(
      values.includes(value)
        ? values.filter((item) => item !== value)
        : [...values, value],
    );
  }
  return (
    <div
      className="multiselect"
      ref={root}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setOpen(false);
          setQuery("");
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
        onClick={() => {
          setOpen(!open);
          setQuery("");
        }}
      >
        <span>{values.length ? values.join(", ") : placeholder}</span>
        <span className="selection-count">{values.length}</span>
        <ChevronDown size={16} />
      </button>
      {open && !disabled && (
        <div
          className="multiselect-panel"
          role="group"
          aria-label={placeholder}
        >
          <input
            ref={search}
            className="multiselect-search"
            type="search"
            aria-label={
              itemLabel === "Textspalte"
                ? "Textspalten suchen"
                : `${label} suchen`
            }
            placeholder="Suchen …"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && matches.length) {
                event.preventDefault();
                toggle(matches[0]);
              }
              if (event.key === "ArrowDown") {
                event.preventDefault();
                root.current
                  ?.querySelector<HTMLInputElement>("input[type=checkbox]")
                  ?.focus();
              }
            }}
          />
          <div className="multiselect-options">
            {matches.map((option) => (
              <label className="multiselect-option" key={option}>
                <input
                  type="checkbox"
                  aria-label={`${itemLabel} ${option}`}
                  disabled={
                    !values.includes(option) &&
                    !!maxSelections &&
                    values.length >= maxSelections
                  }
                  checked={values.includes(option)}
                  onChange={() => toggle(option)}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
          {!matches.length && (
            <p className="multiselect-empty">
              Keine passenden Einträge gefunden.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
