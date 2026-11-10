import { useState } from "react";
import type { ReactNode } from "react";
import { HelpCircle, X } from "lucide-react";
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
