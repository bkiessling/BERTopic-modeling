import { useWorkbench } from "../context/WorkbenchContext";
import type { Row } from "../api";
import { api, post } from "../api";
import { ArrowUpRight, ShieldCheck, X, Link2 } from "lucide-react";
import { Field, Select } from "./index";
export function OpenAIConnectionDialog() {
  const {
    token,
    caps,
    busy,
    error,
    notice,
    setNotice,
    setSettings,
    namingModel,
    setNamingModel,
    perform,
    options,
  } = useWorkbench();
  return (
    <div className="modal-backdrop" onClick={() => setSettings(false)}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="OpenAI-Verbindung"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-heading">
          <span className="small-icon">
            <Link2 size={21} />
          </span>
          <h2>OpenAI-Verbindung</h2>
          <button
            autoFocus
            className="icon-button"
            aria-label="Dialog schließen"
            onClick={() => setSettings(false)}
          >
            <X size={20} />
          </button>
        </div>
        <p className="muted">
          Optional für Themennamen. Das lokale Training funktioniert ohne
          API-Key.
        </p>
        <div className={caps?.key_present ? "alert notice" : "alert neutral"}>
          <ShieldCheck size={17} />
          <span>
            {caps?.key_present
              ? `API-Key erkannt · ${caps.key_source}`
              : "Kein API-Key hinterlegt"}
          </span>
        </div>
        <Field label="Modell für Themennamen">
          <Select
            label="OpenAI-Modell"
            value={namingModel}
            options={Object.entries(caps?.naming_models || {}).map(
              ([value, label]) => ({ value, label: String(label) }),
            )}
            disabled={!caps?.key_present}
            onChange={setNamingModel}
          />
        </Field>
        <button
          className="button secondary"
          disabled={!caps?.key_present || !!busy}
          onClick={() =>
            void perform("api", async () => {
              const value = await api(
                "/openai/check",
                token,
                post({ model: namingModel }),
              );
              setNotice(value.message);
              setSettings(false);
            })
          }
        >
          API-Zugriff prüfen
        </button>
        <div className="setup-note">
          <h3>Key lokal hinterlegen</h3>
          <p>
            In <code>config/secrets.toml</code> im Projektverzeichnis:
          </p>
          <pre>OPENAI_API_KEY = "DEIN_NEUER_API_KEY"</pre>
          <p>
            Alternativ als Umgebungsvariable. Der Key bleibt auf dem
            Python-Server. Nach Änderungen den Server neu starten.
          </p>
          <a
            href="https://platform.openai.com/api-keys"
            target="_blank"
            rel="noreferrer"
          >
            OpenAI API keys
            <ArrowUpRight size={13} />
          </a>
        </div>
        <p className="fineprint">
          ChatGPT Pro beinhaltet keine API-Nutzung. Die Verbindungskontrolle
          prüft die Modellsichtbarkeit, nicht Guthaben oder
          Responses-Berechtigung.
        </p>
        {error && (
          <p role="alert" className="error-text">
            {error}
          </p>
        )}
      </section>
    </div>
  );
}
