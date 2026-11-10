import type { ReactNode } from "react";
import { Help } from "./Help";
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
