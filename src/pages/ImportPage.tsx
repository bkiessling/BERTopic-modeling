import helpText from "../content/help.de.json";
import { ArrowRight } from "lucide-react";
import { useWorkbench } from "../context/WorkbenchContext";
import type { Row } from "../api";
import {
  Check,
  FileSpreadsheet,
  LoaderCircle,
  ShieldCheck,
  UploadCloud,
  Type,
} from "lucide-react";
import { DataTable, Field, Select, MultiSelect } from "../components";
export function ImportPage() {
  const {
    token,
    setStep,
    uploaded,
    cleaned,
    setCleaned,
    busy,
    error,
    textCols,
    setTextCols,
    idCol,
    setIdCol,
    sample,
    setSample,
    stopwords,
    setStopwords,
    file,
    fileInput,
    blocked,
    upload,
    clean,
    sourcePreview,
    options,
  } = useWorkbench();
  return (
    <>
      <section className="section-heading">
        <div>
          <h2>Daten importieren</h2>
        </div>
        <span className="quiet-chip">CSV & Excel</span>
      </section>
      <div className="import-grid">
        <section className="card upload-card">
          <div className="card-title">
            <FileSpreadsheet size={18} />
            <h3>Datenquelle</h3>
          </div>
          <input
            ref={fileInput}
            aria-label="CSV- oder Excel-Datei auswählen"
            type="file"
            accept=".csv,.xlsx"
            hidden
            onChange={(e) => {
              if (e.target.files?.[0]) void upload(e.target.files[0]);
            }}
          />
          <button
            className="dropzone"
            disabled={!token || blocked}
            onClick={() => fileInput.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (token && !blocked && e.dataTransfer.files[0])
                void upload(e.dataTransfer.files[0]);
            }}
          >
            <span className="upload-icon">
              {busy === "upload" ? (
                <LoaderCircle className="spin" size={25} />
              ) : (
                <UploadCloud size={25} />
              )}
            </span>
            <strong>
              {uploaded ? "Datei austauschen" : "Datei hier ablegen"}
            </strong>
            <span>
              oder <b>Datei auswählen</b>
            </span>
            <small>.csv oder .xlsx · bis zu 25 MB</small>
          </button>
          {uploaded && (
            <div className="file-loaded">
              <span className="file-icon">
                <FileSpreadsheet size={20} />
              </span>
              <div>
                <strong>{uploaded.file_name}</strong>
                <p>
                  {uploaded.rows.toLocaleString("de-DE")} Zeilen ·{" "}
                  {uploaded.columns.length} Spalten
                </p>
              </div>
              <Check size={18} />
            </div>
          )}
          {uploaded && !cleaned && (
            <div className="raw-preview">
              <h3>Importvorschau</h3>
              <p className="muted">
                Die ersten drei Zeilen mit allen Spalten. Stimmen Trennzeichen
                und Inhalte?
              </p>
              <DataTable rows={uploaded.preview.slice(0, 3)} />
            </div>
          )}
          {file?.name.toLowerCase().endsWith(".csv") && (
            <Field label="CSV-Trennzeichen">
              <Select
                label="CSV-Trennzeichen"
                value={uploaded?.delimiter || ","}
                options={[
                  { value: ",", label: "Komma ( , )" },
                  { value: ";", label: "Semikolon ( ; )" },
                  { value: "\t", label: "Tabulator" },
                ]}
                disabled={blocked}
                onChange={(value) => void upload(file, value)}
              />
            </Field>
          )}
        </section>
        <section className="card selection-card">
          <div className="card-title">
            <Type size={18} />
            <h3>Texte auswählen</h3>
          </div>
          {uploaded ? (
            <>
              <div className="column-fields">
                <Field label="ID-Spalte" help={helpText.idColumn}>
                  <Select
                    label="ID-Spalte"
                    value={idCol}
                    options={options([
                      "ID generieren",
                      ...uploaded.columns.filter(
                        (col: string) => !textCols.includes(col),
                      ),
                    ])}
                    disabled={blocked}
                    onChange={(v) => {
                      setIdCol(v);
                      setCleaned(null);
                    }}
                  />
                </Field>
                <Field label="Textspalte(n)" help={helpText.textColumns}>
                  <MultiSelect
                    label="Textspalte(n)"
                    values={textCols}
                    options={uploaded.text_columns}
                    disabled={blocked}
                    onChange={(values) => {
                      setTextCols(values);
                      if (values.includes(idCol)) setIdCol("ID generieren");
                      setCleaned(null);
                    }}
                  />
                  {!uploaded.text_columns.length && (
                    <p className="error-text">
                      Keine Textspalten gefunden. Trennzeichen prüfen.
                    </p>
                  )}
                </Field>
              </div>
              <div className="two-fields">
                <Field label="Stichprobe (%)">
                  <input
                    aria-label="Stichprobe (%)"
                    type="number"
                    min={1}
                    max={100}
                    value={sample}
                    disabled={blocked}
                    onChange={(e) => {
                      setSample(+e.target.value);
                      setCleaned(null);
                    }}
                  />
                </Field>
                <Field label="Zusätzliche Stopwörter" help={helpText.stopwords}>
                  <input
                    aria-label="Zusätzliche Stopwörter"
                    placeholder="z. B. newsletter, firma"
                    value={stopwords}
                    disabled={blocked}
                    onChange={(e) => {
                      setStopwords(e.target.value);
                      setCleaned(null);
                    }}
                  />
                </Field>
              </div>
              <div className="selection-actions">
                <button
                  className="button primary full"
                  disabled={
                    blocked || !textCols.length || sample < 1 || sample > 100
                  }
                  onClick={() => void clean()}
                >
                  Daten bereinigen
                </button>
              </div>
            </>
          ) : (
            <div className="placeholder">
              <span className="placeholder-glyph">
                <Type size={28} />
              </span>
              <p>
                Deine Textspalten erscheinen hier,
                <br />
                sobald eine Datei importiert ist.
              </p>
            </div>
          )}
        </section>
      </div>
      {(uploaded || cleaned) && (
        <section className="card preview-card">
          <div className="preview-heading">
            <div>
              <h3>
                {cleaned ? "Daten für die Modellierung" : "Datenvorschau"}
              </h3>
              <p>
                {cleaned
                  ? "ID-Spalte und bereinigte Texte, die zur Modellierung genutzt werden."
                  : "Ausgewählte Spalten · erste acht Zeilen."}
              </p>
            </div>
            {cleaned && (
              <span className="success-chip">
                <Check size={13} />
                Bereinigt
              </span>
            )}
          </div>
          {cleaned && (
            <div className="mini-stats">
              <div>
                <strong>{cleaned.rows.toLocaleString("de-DE")}</strong>
                <span>verwendbare Texte</span>
              </div>
              <div>
                <strong>{cleaned.rows_before - cleaned.rows}</strong>
                <span>entfernte Texte</span>
              </div>
              <div>
                <strong>{cleaned.average_length}</strong>
                <span>Ø Zeichen / Text</span>
              </div>
            </div>
          )}
          <DataTable
            rows={
              cleaned
                ? cleaned.preview.map((row: Row) => ({
                    ID: row.id,
                    [textCols.length === 1 && textCols[0] !== "ID"
                      ? textCols[0]
                      : "Text"]: row.text,
                  }))
                : sourcePreview
            }
          />
        </section>
      )}
      <div className="action-bar">
        <span>
          <ShieldCheck size={15} />
          Deine Daten werden lokal verarbeitet.
        </span>
        <button
          className="button next-step"
          disabled={!cleaned || blocked}
          onClick={() => setStep(1)}
        >
          Weiter zur Modellierung <ArrowRight size={16} />
        </button>
      </div>
    </>
  );
}
