# Topic Modeling mit BERTopic

Interaktive Streamlit-Anwendung für explorative Themenanalysen deutscher und englischer Texte. CSV- und Excel-Dateien werden hochgeladen, bereinigt, mit BERTopic modelliert und anschließend als Tabellen und Plotly-Diagramme untersucht.

## Installation

Getestet unter Linux mit Python 3.12. Auf macOS den CPU-Index-Schritt auslassen; PyTorch wird dort aus `requirements.txt` installiert. Die App nutzt verfügbare CUDA- bzw. Apple-MPS-Beschleunigung, sonst CPU. Eine virtuelle Umgebung wird empfohlen:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
# Für Linux ohne GPU zuerst die CPU-Variante installieren:
python -m pip install 'torch==2.15.0' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m nltk.downloader stopwords
```

Die direkten Abhängigkeiten sind auf getestete Versionen festgelegt. `requirements.txt` ist kein vollständiges Lockfile für transitive Abhängigkeiten. Für eine GPU-Installation die passende PyTorch-Variante gemäß [PyTorch](https://pytorch.org/get-started/locally/) installieren.

NLTK verwendet ein lokales Stopwort-Korpus. In der verwalteten Codex-Cloud kann dafür `NLTK_DATA=/workspace/.bertopic-setup/nltk_data` verwendet werden. Der dortige richtliniengesteuerte Proxy benötigt für den NLTK-Downloader zusätzlich `NLTK_ALLOW_PROXIED_URLOPEN=1`; TLS-Prüfung bleibt aktiv.

## Start und Nutzung

Im Repository-Verzeichnis:

```bash
streamlit run app.py
```

1. **Upload und Bereinigung:** UTF-8-CSV oder `.xlsx` hochladen, ID- und Textspalten wählen, bei Bedarf Stichprobe und zusätzliche zu entfernende Wörter angeben. Mehrere Textspalten werden untereinander angeordnet. Anschließend „Daten bereinigen“ klicken.
2. **Modellierung:** Sprache, Embedding-Modell sowie UMAP-, HDBSCAN- und Vektorisierungsparameter wählen. „Modell trainieren“ lädt das Sprachmodell und startet das Training.
3. **Analyse:** Themen und Dokumentzuordnungen prüfen, Ausreißer optional neu zuordnen oder zurücksetzen, Ähnlichkeitsmatrix, Keywords und Dokumentenkarte untersuchen.

Die Bereinigung entfernt unter anderem URLs, Zahlen und Satzzeichen und wandelt Texte in Kleinbuchstaben um. Das kann fachlich wichtige Informationen entfernen; die Vorschau vor dem Training prüfen. Für belastbare Themenanalysen genügend vielfältige Texte verwenden; sehr kleine Datensätze liefern häufig keine stabilen Cluster.

Neue bereinigte Daten verwerfen das bisherige Modell der Sitzung. Ein Browser-Neustart bzw. eine neue Streamlit-Sitzung kann Ergebnisse verlieren; Ergebnisse können als ZIP heruntergeladen werden. Ein Modellimport und das Speichern/Laden eines trainierten Modells sind derzeit nicht implementiert.

### Netzwerk und Modelle

Pakete kommen von PyPI und gegebenenfalls `download.pytorch.org`. NLTK lädt Stopwörter von `raw.githubusercontent.com`. Die Embedding-Modelle werden bei erster Verwendung von Hugging Face heruntergeladen und lokal zwischengespeichert. Öffentliche Modelle benötigen grundsätzlich keinen API-Key.

In eingeschränkten Cloud-Netzen müssen `huggingface.co` und die tatsächlichen Download-/Redirect-Ziele zugelassen sein, gegebenenfalls `*.huggingface.co` sowie die verwendeten Xet-CDN-Hosts. In der aktuellen Cloud-Umgebung war Hugging Face beim Prüfen mit HTTP 403 blockiert. Die Tests nutzen deshalb lokale synthetische Embeddings; Modell-Downloads und die semantische Qualität der realen Embeddings wurden damit nicht geprüft.

Die Auswahl beginnt bei der Sprache: Für Deutsch werden mehrsprachiges MiniLM (Voreinstellung) und mehrsprachiges MPNet angeboten. Für Englisch stehen zusätzlich englisches MiniLM (Voreinstellung) und MPNet bereit. Die Textlänge ändert das Sprachmodell nicht. Modellwahl und Clusteringqualität müssen weiterhin fachlich geprüft werden. Modellcode aus fremden Repositories wird nicht ausgeführt (`trust_remote_code=False`); Jina ist deshalb nicht mehr Bestandteil der Standardauswahl.

## Ergebnisexport

In der Analyse unter **Ergebnisse exportieren** das ZIP-Archiv herunterladen:

- `documents.csv` / `documents.json`: IDs, bereinigte Texte und aktuelle Themenzuordnungen, einschließlich Ausreißeränderungen.
- `topics.csv` / `topics.json`: Themenhäufigkeiten und Repräsentationen.
- `manifest.json`: Trainingsparameter, Seed, Paketversionen, Zeitstempel, Textspalten, Bereinigungseinstellungen und angewendete Ausreißerschwellwerte.

CSV-Dateien verwenden UTF-8 mit BOM. Texte mit Formelpräfix werden für Tabellenkalkulationen mit einem Apostroph geschützt; JSON enthält die unveränderten Werte. Das Archiv enthält Texte aus dem Upload, aber weder die ursprüngliche Datei noch ausführbare Modellobjekte. Es dient der Ergebnisweitergabe, nicht dem Wiederaufnehmen des Trainings. Seed und Metadaten garantieren keine hardwareübergreifend identischen Ergebnisse.

## Parameterprüfung und Trainingsschnittstelle

Die Oberfläche meldet ungültige Parameter und deaktiviert das Training, bevor ein Sprachmodell geladen wird. Die Trainingsfunktion prüft dieselben Regeln unabhängig von Streamlit: mindestens vier nichtleere Texte, gültige UMAP-Dimensionen/Nachbarzahlen, Clustergröße, N-Gramme, Häufigkeitsgrenzen, Sprache und Themenrepräsentationen. Vier Texte sind eine technische Untergrenze, keine Empfehlung für belastbare Analysen.

Die Vektorisierung prüft auf leeres Vokabular. BERTopic wendet `min_df`/`max_df` auf nach Themen zusammengefasste Texte an; nach dem Clustering kann daher zusätzlich eine verständliche Fehlermeldung notwendig sein. `max_df=1.0` vermeidet unbeabsichtigtes Entfernen aller Begriffe bei wenigen Themen.

`TrainingConfig` und `TrainingResult` bilden die unabhängige Schnittstelle:

```python
from modules.modeling.configuration import TrainingConfig, MULTILINGUAL_MODEL
from modules.modeling.train_model import train_bertopic_model

config = TrainingConfig(MULTILINGUAL_MODEL, "Deutsch")
# documents: Liste ausreichend vieler Texte; encoder: bereits geladenes Embedding-Modell
result = train_bertopic_model(documents, config, encoder,
                             on_progress=lambda percent, message: print(percent, message))
# result.model, result.topic_info, result.embeddings, result.documents, result.config
```

Das Training importiert kein Streamlit und schreibt nicht in `session_state`. Die Oberfläche speichert Modell und Auswertungszustand in einem `AnalysisState`-Objekt unter einem Sitzungsschlüssel. Die Ausreißerfunktionen sind ebenfalls unabhängig von Streamlit. Widgets bleiben in `modules/ui/modeling_inputs.py`.

## Aktualisieren und Importfehler

Nach einem Branch-Wechsel oder Update den laufenden Streamlit-Prozess mit `Ctrl+C` beenden und neu starten:

```bash
git switch dev
git pull --ff-only
python -m pip install -r requirements.txt
streamlit run app.py
```

Ein `ImportError` für `restore_outliers` kann auf einen älteren Checkout oder ein noch geladenes altes Python-Modul hinweisen. Der aktuelle Stand enthält die Funktion; ein Neustart lädt die neue Version. Laufende Sitzungen mit alten Ergebnisobjekten müssen nach dieser Umstellung neu trainiert werden.

## Diagramme interpretieren

- **Themen-Ähnlichkeit:** Kosinus-Ähnlichkeit der Themen-Embeddings, kein statistischer z-Wert. Die häufigsten maximal 20 Themen werden angezeigt; Ausreißer (`-1`) bleiben ausgeschlossen.
- **Top-Keywords:** Bis zu vier Themen auswählen. Die Gewichte hängen von der gewählten Themenrepräsentation ab und sind keine Wahrscheinlichkeiten.
- **Dokumentenkarte:** Jeder Punkt steht für ein Dokument. UMAP projiziert Embeddings in zwei Dimensionen; Farben zeigen Topic-Zuordnungen. Abstände sind explorativ zu interpretieren. Es handelt sich nicht um einen Graphen mit Kanten. Seltene Themen sind gegebenenfalls zunächst nur in der Legende sichtbar. Kleine Datensätze verwenden eine einfache PCA-Projektion; identische Embeddings können überlappende Punkte erzeugen.

Das Layout wird unabhängig von den Themenlabels zwischengespeichert. Alle Streamlit-Tabs werden bei einem Seitenlauf ausgeführt, auch wenn gerade nur einer sichtbar ist.

## Tests

Aus dem Repository-Verzeichnis:

```bash
HF_HUB_OFFLINE=1 NUMBA_NUM_THREADS=2 OMP_NUM_THREADS=2 \
  python -m unittest discover -s tests -v
```

Die Tests benötigen keine heruntergeladenen Sprachmodelle. Sie prüfen Plotly-Kompatibilität, ausschließlich Ausreißer, kleine Datensätze, echtes BERTopic-Training mit synthetischen Embeddings, das Rendern aller drei Diagramme über Streamlit `AppTest`, erneute Seitenausführung sowie konsistentes Zurücksetzen von Ausreißern. Hinzu kommen Parameterprüfung vor dem Encoding, sprachabhängige Modellauswahl, der deaktivierte Trainingsbutton bei ungültigen Eingaben und der ZIP-/CSV-/JSON-Export. Die englische Stopwortliste des Testtrainings ist in scikit-learn enthalten. Der erste Lauf kann wegen der Numba-Kompilierung länger dauern.

## Repository-Struktur

```text
app.py                      Streamlit-Einstieg und Weiterleitung
pages/                      Upload, Modellierung und Analyse
modules/
  upload/                   Dateiformate und CSV-Trennzeichen
  preprocessing/            Textauswahl, Bereinigung und Stopwörter
  modeling/                 Unabhängige Konfiguration, Validierung und Training
  analysis/                 Tabellen, Ausreißerbehandlung und Ergebnisexport
  viz/                      Diagramme und gecachte Projektion
  ui/                       Widgets, Erläuterungen und Analyse-Sitzungszustand
assets/                     Logo
.streamlit/config.toml      Darstellung und Streamlit-Einstellungen
tests/                      Regressionstests und Streamlit-Integration
requirements.txt            Getestete direkte Python-Abhängigkeiten
```

Die Trennung nach Arbeitsschritten ist für die aktuelle Größe sinnvoll. Trainings- und Analyselogik sind von der Streamlit-Sitzung getrennt; nur Seiten und UI-Adapter verwalten den Oberflächenzustand. `topic_modeling.py` ist ein älterer Einstieg; unterstützt wird `app.py`. `modules/viz/heatmap.py` enthält eine weitere, derzeit nicht eingebundene Wortgewichtungsansicht.

## Eignung und nächste Schritte

Streamlit eignet sich für explorative Analysen, interne Fachanwendungen und einen kleinen Nutzerkreis. Eine Migration ist dafür nicht nötig. Für lange, parallele Trainingsjobs und einen öffentlich betriebenen Mehrbenutzerdienst fehlen derzeit Hintergrundjobs, persistente Ergebnisse, Fortschritts-/Fehlerverwaltung außerhalb der Browser-Sitzung und ein Betriebskonzept für Authentifizierung und Ressourcenlimits.

Prioritäten für die weitere Entwicklung:

- Die sprachlich passende Modellauswahl an eigenen Beispieldaten evaluieren und Modellrevisionen festlegen.
- Qualitätsmaße für Themen ergänzen; technische Parameterprüfung ersetzt keine fachliche Evaluation.
- Fehlgeschlagene Uploads mit verständlichen Meldungen behandeln, Zeichencodierung und Datenqualität prüfen.
- Wiederladbaren Modellexport und ein vollständiges Lockfile ergänzen; ungenutzte Einstiege und Module konsolidieren.
- Bei großen Datenmengen Projektionen begrenzen bzw. gezielt berechnen und Training in einen Hintergrundprozess auslagern.
