import { Help } from "./Help";
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
