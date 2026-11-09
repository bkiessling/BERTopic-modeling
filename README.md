# BERTopic · #NDRfragt Topic Modeling

Lokale Themenanalyse mit **React/TypeScript**, **FastAPI** und **BERTopic**. Texte importieren, Modelle konfigurieren und Ergebnisse untersuchen – ohne Sidebar. Die aktuelle Anwendung liegt im Branch `feature/react-workbench`.

![Modellierung mit Parameterkarten](docs/screenshots/react-modeling.png)

## Schnellstart auf deinem Mac

Voraussetzungen: **Python 3.11 oder 3.12** und **Node.js 22 oder neuer**. Eine eigene Conda-Umgebung verhindert Konflikte mit `(base)`.

```bash
git fetch origin
git switch feature/react-workbench
git pull --ff-only
conda activate bertopic-dev
python -m pip install -r requirements.txt
python -m nltk.downloader stopwords
npm --prefix frontend ci
npm --prefix frontend run build
python -m backend
```

Falls die Conda-Umgebung noch nicht existiert: `conda create -n bertopic-dev python=3.11 pip`, dann aktivieren. Falls der Branch nur remote existiert: `git switch --track origin/feature/react-workbench`.

Die App läuft auf deinem Rechner unter `http://127.0.0.1:8000`. Ein Python-Prozess liefert API und gebautes Frontend aus; Node ist im normalen Betrieb nicht nötig. `./scripts/start-web.sh` ist ein kurzer Alias für denselben Start. Nach Frontend-Änderungen erneut `npm --prefix frontend run build` ausführen. Den Server nach Python-/Konfigurationsänderungen neu starten. Bestehende Modelle im RAM gehen dabei verloren.

**Linux ohne GPU:** Vor der Installation der Requirements bei Bedarf die CPU-Variante vorinstallieren:

```bash
python -m pip install 'torch==2.15.0' --index-url https://download.pytorch.org/whl/cpu
```

Auf Intel-macOS wählt `requirements.txt` automatisch PyTorch 2.2.2, NumPy 1.26 und dazu passende Versionen von Pandas, SciPy und Numba. Keinen Linux-CPU-Index auf dem Mac verwenden. Python 3.11 und 3.12 werden berücksichtigt; native Mac-Tests sind in der CI eingerichtet, die Cloud führt selbst Linux aus.

## Arbeitsablauf

### 1. Import

CSV (UTF-8) oder Excel hochladen, Trennzeichen prüfen und zuerst eine ID-Spalte wählen oder IDs generieren lassen. Danach die Textspalte(n) im durchsuchbaren Multiselect auswählen. Es gibt keine automatische Vorauswahl. Mehrere Textspalten werden für das Training untereinander angeordnet.

Die Originalvorschau zeigt zuerst die ID-Spalte und danach nur ausgewählte Textspalten. Bei „ID generieren“ bleibt die ID-Spalte dort zunächst leer. Nach „Daten bereinigen“ ersetzt die Vorschau die Originalwerte direkt durch die tatsächlich verwendeten bereinigten Texte einschließlich ihrer IDs.

Stichprobe und zusätzliche, durch Komma getrennte Stopwörter sind optional. Die Bereinigung entfernt URLs, Erwähnungen, Zahlen und Satzzeichen, wandelt in Kleinbuchstaben um und entfernt leere Texte. Dabei können fachlich wichtige Informationen verloren gehen; Vorschau prüfen.

### 2. Modellierung

Oben stehen drei Kacheln: **Voreinstellungen**, die breitere **Sprache & Embeddings**-Auswahl und **Themen automatisch benennen**. Darunter liegen UMAP, HDBSCAN/Themenbeschreibung und Vektorisierung. Kleine Info-Buttons erklären Parameter bei Bedarf.

Die Web-API behandelt `min_df` und `max_df` ausdrücklich als **Anteile zwischen 0 und 1**. Insbesondere wird JSON `max_df: 1` als `1.0` / 100 % interpretiert, nicht als absolute Häufigkeit 1. BERTopic wendet die Filter auf zusammengefasste Themen-Texte an. Ein zu hoher Mindestwert oder fehlendes Vokabular kann nach dem Clustering weiterhin eine sinnvolle Fehlermeldung auslösen.

Das lokale Training läuft als Hintergrundjob mit Fortschritt. Ungültige Parameter werden vor dem Laden des Sprachmodells geprüft. Ein fehlgeschlagenes Folgetraining verwirft vorherige Ergebnisse nicht. Änderungen an Formularwerten verändern kein bereits trainiertes Modell.

### 3. Ergebnisse

- Themen, Keywords und optional generierte Themennamen.
- Suchbare Dokumenttabelle mit Pagination und Gruppierung nach ID.
- Tatsächlich verwendete Trainingsparameter.
- Kosinus-Ähnlichkeitsmatrix der häufigsten Themen, Keyword-Balken für bis zu vier Themen und Dokumentenkarte mit UMAP oder t-SNE.
- Ausreißer reduzieren und ursprüngliche Zuordnungen wiederherstellen.
- ZIP-Export mit Dokumenten-/Thementabellen als CSV und JSON sowie Parametern und Paketversionen.

Kosinus-Ähnlichkeit ist kein statistischer z-Wert. Keyword-Gewichte sind keine Wahrscheinlichkeiten. Eine zweidimensionale Dokumentenkarte ist explorativ zu interpretieren. Ein Seed garantiert keine hardwareübergreifend bitgleichen Ergebnisse.

## OpenAI: optionale Themennamen

Der Dialog über die Verbindungsschaltfläche oben rechts enthält Modell-Dropdown und **API-Zugriff prüfen**. Die Benennung ist standardmäßig aus und ohne Key deaktiviert. Sie lässt sich beim Training oder nachträglich mit Keyword-Vorschau auslösen. **ChatGPT Pro beinhaltet keine API-Nutzung**; API-Key und Abrechnung werden separat auf der [OpenAI Platform](https://platform.openai.com/api-keys) verwaltet.

Neue lokale Schlüssel in **`config/secrets.toml`** speichern:

```toml
OPENAI_API_KEY = "DEIN_VOLLSTÄNDIGER_OPENAI_API_KEY"
```

`config/secrets.example.toml` ist eine Vorlage ohne Schlüssel. Die echte Datei ist von Git ausgeschlossen. Alternativ sind `BERTOPIC_OPENAI_API_KEY` oder `OPENAI_API_KEY` als Umgebungsvariable möglich. Projektdatei hat Vorrang vor globaler Konfiguration in `~/.config/bertopic-workbench/secrets.toml`, danach folgen Umgebungsvariablen. Der Browser erhält nur Anwesenheit und Quellenname, **niemals den Schlüssel**. Keine API-Keys in React oder `VITE_*`-Variablen eintragen.

**Umstieg von der alten App:** `python -m backend` übernimmt eine vorhandene `.streamlit/secrets.toml` einmalig nach `config/secrets.toml` mit Dateirechten `0600`. Eine vorhandene neue Konfiguration wird niemals überschrieben; die alte Datei bleibt unverändert. Die Migrationshilfe benötigt kein Streamlit. Es gibt keine alte Streamlit-Anwendung oder entsprechende Laufzeitabhängigkeit mehr.

Die Benennung sendet nur Themen-IDs, bis zu zehn Keywords je Thema, Sprache und Benennungsanweisungen an OpenAI. Originaldateien, Dokumenttexte, Dokument-IDs und Embeddings bleiben lokal. **Keywords können trotzdem Namen oder vertrauliche Begriffe enthalten.** `store=false` ist gesetzt; es gelten weiterhin die [API-Datenregeln](https://platform.openai.com/docs/guides/your-data).

API-Kontrolle fragt nur Modell-Metadaten ab und generiert keine Antwort. Erfolg bestätigt nicht Guthaben oder Responses-Berechtigung. HTTP 401 bedeutet, dass der gefundene Wert abgelehnt wurde: echte aktive OpenAI-Platform-Keys statt Platzhaltern verwenden und angezeigte Quelle prüfen. API-Fehler erhalten das lokale Modell. Ein normaler UI-Rerender verursacht keine neue Benennung. Explizite erneute Benennung kann Kosten verursachen, auch wenn ein späteres Paket fehlschlägt. Nach Ausreißeränderungen werden alte KI-Namen verworfen.

## Struktur

```text
frontend/
  src/App.tsx              Schlanke Anwendungshülle und Navigation
  src/features/            Import, Modellierung, Ergebnisse, Verbindung
  src/state/               Gemeinsamer Workflow-Zustand
  src/components.tsx       Controls, Multiselect, Hilfen, Tabellen, Diagramme
  src/api.ts               HTTP-Client und Typen
  src/style.css            Design und responsive Darstellung
  e2e/                     Browser-Tests
backend/
  __main__.py              Lokaler Start, sichere Konfigurationsmigration
  app.py                   App-Zusammenbau und statisches Hosting
  routes/                  Endpunkte für System, Import, Training und Ergebnisse
  schemas.py               Validierte Request-Schemas
  runtime.py               Sitzungen, Job-Queue, Encoder-Cache
  settings.py              Serverkonfiguration und Zugangsdaten
  migrate.py               Einmalige, nicht überschreibende Migration
modules/
  modeling/                Unabhängige Konfiguration, Encoder und Training
  preprocessing/           Textauswahl und Bereinigung
  upload/                  CSV-Trennzeichenerkennung
  analysis/                Ergebniszustand, Tabellen, Export, OpenAI-Benennung
  viz/                     Frameworkfreie Plotly-Diagramme und Projektion
config/                    Vorlage und ignorierte lokale Secrets
scripts/                   Starthelfer
tests/unit/                Fachlogik und Datenfluss
tests/api/                 HTTP-Integration einschließlich echtem Testtraining
tests/fixtures/            Ausschließlich für Tests: Offline-Encoder-Server
```

React bleibt für Darstellung und Bedienung zuständig. Modellierung und Analyse sind unabhängig vom Frontend. FastAPI übersetzt HTTP-Anfragen in Fachoperationen; die Jobverwaltung ist davon getrennt. Plotly wird erst bei Bedarf geladen. Die ursprünglichen fachlichen Module wurden weiterverwendet, ungenutzte Einstiege, Widgets und alte Tests entfernt.

## Entwicklung und Tests

Backend: `python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`. Frontend in einem zweiten Terminal: `npm --prefix frontend run dev`. Vite läuft auf Port 5173 und leitet `/api` zum Backend weiter.

```bash
HF_HUB_OFFLINE=1 NUMBA_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m unittest discover -s tests -v
npm --prefix frontend run build
cd frontend
npx playwright install chromium
npm run test:e2e
```

Die Browser-Tests starten selbst `tests.fixtures.server` mit lokal erzeugten Test-Embeddings. Der reguläre Server verwendet echte Sprachmodelle. Tests prüfen Datenfluss, JSON-Zahlensemantik, Konfigurationsmigration, API-Fehler, Diagramme, Suche, Download, Reload sowie Desktop/Mobil. Sie benötigen weder vortrainierte Modell-Downloads noch API-Guthaben. Modellqualität und echte API-Zugriffe sind damit nicht belegt.

## Betrieb und Grenzen

Die App ist für lokalen Betrieb mit **einem Python-Worker** ausgelegt. Jobs laufen nacheinander. Sitzungen und Modelle liegen im RAM; ein Seiten-Reload findet sie wieder, ein Serverneustart nicht. Maximal 20 ruhende Arbeitsbereiche und 25 MB je Upload begrenzen den lokalen Datenumfang. Nach zwei Stunden ruhende Sitzungen werden bei der nächsten Neuanlage entfernt. Große Modelle benötigen dennoch viel RAM.

Abbrechen/Wiederaufnehmen laufender Jobs, dauerhaft gespeicherte Modelle, Login und verteilte Worker sind nicht implementiert. Für einen öffentlichen Mehrbenutzerdienst wäre ein gesondertes Betriebskonzept erforderlich. Deshalb ist der Standardstart auf `127.0.0.1` gebunden.

Details zur Modellauswahl: [Embedding-Modelle für Deutsch](docs/embedding-models.md). In eingeschränkten Netzen müssen Modell-Downloads von Hugging Face und optional `api.openai.com` erreichbar sein. MiniLM oder E5 small sind praktische Ausgangspunkte auf einem Intel-Mac; ein Leaderboard-Gesamtwert ersetzt keine Bewertung der eigenen Themen.
