import type { Row } from "../api";
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
