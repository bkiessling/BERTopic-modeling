import type { Row } from "../api";
export function DataTable({
  rows,
  sort,
  descending,
  onSort,
}: {
  rows: Row[];
  sort?: string;
  descending?: boolean;
  onSort?: (column: string) => void;
}) {
  if (!rows.length)
    return <div className="empty-inline">Keine Einträge vorhanden.</div>;
  const cols = Object.keys(rows[0]);
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
      <table>
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
