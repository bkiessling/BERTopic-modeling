import { useRef, useState } from "react";
import type { Row } from "../api";
const savedWidths = new Map<string, Record<string, number>>();
const initialWidth = (column: string) =>
  column === "ID" || column === "Thema"
    ? 90
    : column === "Textbeitrag"
      ? 420
      : column === "Themenname"
        ? 250
        : column === "Keywords"
          ? 280
          : 180;
const clampWidth = (width: number) =>
  Math.min(1200, Math.max(72, Math.round(width)));

export function DataTable({
  rows,
  tableKey,
  sort,
  descending,
  onSort,
}: {
  rows: Row[];
  tableKey?: string;
  sort?: string;
  descending?: boolean;
  onSort?: (column: string) => void;
}) {
  const [widths, setWidths] = useState<Record<string, number>>(() =>
    tableKey ? savedWidths.get(tableKey) || {} : {},
  );
  const drag = useRef<{ column: string; startX: number; width: number } | null>(
    null,
  );
  function resize(column: string, width: number) {
    setWidths((previous) => {
      const next = { ...previous, [column]: clampWidth(width) };
      if (tableKey) savedWidths.set(tableKey, next);
      return next;
    });
  }
  const cols = rows.length ? Object.keys(rows[0]) : [];
  function freezeWidths(handle: HTMLElement) {
    const row = handle.parentElement!.parentElement!;
    const actual = Object.fromEntries(
      cols.map((column, index) => [
        column,
        row.children[index].getBoundingClientRect().width,
      ]),
    );
    setWidths(actual);
    if (tableKey) savedWidths.set(tableKey, actual);
    return actual;
  }
  if (!rows.length)
    return <div className="empty-inline">Keine Einträge vorhanden.</div>;

  const display = (v: any) =>
    v == null
      ? "—"
      : typeof v === "boolean"
        ? v
          ? "Ja"
          : "Nein"
        : Array.isArray(v)
          ? v.filter((item) => item != null && item !== "").join(", ")
          : typeof v === "object"
            ? JSON.stringify(v)
            : String(v);
  return (
    <div className="table-wrap">
      <table
        className="resizable-table"
        style={{
          minWidth: Object.keys(widths).length ? 0 : "100%",
          width: cols.reduce(
            (sum, column) => sum + (widths[column] || initialWidth(column)),
            0,
          ),
        }}
      >
        <colgroup>
          {cols.map((column) => (
            <col
              key={column}
              style={{ width: widths[column] || initialWidth(column) }}
            />
          ))}
        </colgroup>
        <thead>
          <tr>
            {cols.map((c) => (
              <th
                key={c}
                aria-sort={
                  onSort
                    ? sort === c
                      ? descending
                        ? "descending"
                        : "ascending"
                      : "none"
                    : undefined
                }
              >
                {onSort ? (
                  <button className="table-sort" onClick={() => onSort(c)}>
                    {c}
                    <span aria-hidden="true">
                      {sort === c ? (descending ? " ↓" : " ↑") : " ↕"}
                    </span>
                  </button>
                ) : (
                  c
                )}
                <span
                  className="column-resizer"
                  role="separator"
                  tabIndex={0}
                  aria-orientation="vertical"
                  aria-label={`Spaltenbreite ${c}`}
                  aria-valuemin={72}
                  aria-valuemax={1200}
                  aria-valuenow={widths[c] || initialWidth(c)}
                  onClick={(event) => event.stopPropagation()}
                  onDoubleClick={() => resize(c, initialWidth(c))}
                  onPointerDown={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    const actual = freezeWidths(event.currentTarget);
                    drag.current = {
                      column: c,
                      startX: event.clientX,
                      width: actual[c],
                    };
                    event.currentTarget.setPointerCapture(event.pointerId);
                  }}
                  onPointerMove={(event) => {
                    if (drag.current?.column === c)
                      resize(
                        c,
                        drag.current.width +
                          event.clientX -
                          drag.current.startX,
                      );
                  }}
                  onPointerUp={(event) => {
                    drag.current = null;
                    if (event.currentTarget.hasPointerCapture(event.pointerId))
                      event.currentTarget.releasePointerCapture(
                        event.pointerId,
                      );
                  }}
                  onLostPointerCapture={() => {
                    drag.current = null;
                  }}
                  onKeyDown={(event) => {
                    if (
                      ["ArrowLeft", "ArrowRight", "Home", "End"].includes(
                        event.key,
                      )
                    ) {
                      event.preventDefault();
                      event.stopPropagation();
                      const width = freezeWidths(event.currentTarget)[c];
                      resize(
                        c,
                        event.key === "Home"
                          ? 72
                          : event.key === "End"
                            ? 1200
                            : width + (event.key === "ArrowRight" ? 10 : -10),
                      );
                    }
                  }}
                />
              </th>
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
