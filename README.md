# Topic Modeling mit BERTopic

Interaktive Streamlit-Anwendung für explorative Themenanalysen deutscher und englischer Texte. CSV- und Excel-Dateien werden hochgeladen, bereinigt, mit BERTopic modelliert und anschließend als Tabellen und Plotly-Diagramme untersucht.

## Installation

Python 3.11 und 3.12 werden berücksichtigt. Unter Linux wurde die App mit Python 3.12 geprüft; für Intel-macOS mit Python 3.11 sind zusätzlich passende Binärpakete aufgelöst und der ältere numerische Paketstand unter Linux getestet. Native Mac-Tests laufen in der CI; die Cloud selbst führt kein macOS aus. Die App nutzt verfügbare CUDA- bzw. Apple-MPS-Beschleunigung, sonst CPU. Eine virtuelle Umgebung wird empfohlen:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
# Für Linux ohne GPU zuerst die CPU-Variante installieren:
python -m pip install 'torch==2.15.0' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m nltk.downloader stopwords
```

**Intel-Mac mit Conda / Python 3.11:** Eine separate Umgebung vermeidet Konflikte mit bereits installierten Paketen in `(base)`:

```bash
conda create -n bertopic-dev python=3.11 pip
conda activate bertopic-dev
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m nltk.downloader stopwords
python -m streamlit run app.py
```

`requirements.txt` wählt auf Intel-macOS automatisch NumPy 1.26, Pandas 2.2, PyTorch 2.2.2 sowie passende SciPy-/Numba-/PyArrow-Versionen. Neuere PyTorch-Versionen stellen keine Intel-macOS-Wheels bereit; PyTorch 2.2 benötigt für zuverlässige NumPy-Integration NumPy 1.x. Auf anderen Plattformen mit Python 3.11 wird NumPy 2.4 statt des erst ab Python 3.12 verfügbaren NumPy 2.5 verwendet. Auf macOS **keinen** Linux-PyTorch-CPU-Index angeben und keine neuere PyTorch-Version manuell vorinstallieren.

Die direkten Abhängigkeiten sind auf geprüfte Versionen festgelegt. `requirements.txt` ist kein vollständiges Lockfile für transitive Abhängigkeiten. Für eine GPU-Installation die passende PyTorch-Variante gemäß [PyTorch](https://pytorch.org/get-started/locally/) installieren.

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

Die Auswahl beginnt bei der Sprache. Für Deutsch bietet das Dropdown sechs Modelle: mehrsprachiges MiniLM und MPNet, multilingual E5 small und base, BGE-M3 sowie Qwen3 Embedding 0.6B (experimentell). Unter dem Dropdown stehen Anzahl, Ressourcenhinweis und ein Link zur Modellkarte. Die Textlänge ändert das Sprachmodell nicht. Für Englisch stehen zusätzlich die englischen MiniLM-/MPNet-Varianten bereit. Pro Trainingslauf wird ein Modell verwendet.

E5 erhält automatisch `query: `, Qwen eine Clustering-Instruktion. Kleinere Batches begrenzen den Speicherbedarf der größeren Modelle. Die App fordert Safetensors-Gewichte an (`use_safetensors=True`) und verwendet kein fremdes Modellskript (`trust_remote_code=False`).

Eine Einordnung der deutschen MTEB-Ergebnisse und der Grenzen der Modellprüfung steht in [Embedding-Modelle für Deutsch](docs/embedding-models.md). Ein Gesamtmittel über verschiedene Aufgaben ist kein Beleg für das beste Topic-Clustering. Für deinen Intel-Mac sind MiniLM oder E5 small praktische Ausgangspunkte.

## Ergebnisexport

In der Analyse unter **Ergebnisse exportieren** das ZIP-Archiv herunterladen:

- `documents.csv` / `documents.json`: IDs, bereinigte Texte und aktuelle Themenzuordnungen, einschließlich Ausreißeränderungen.
- `topics.csv` / `topics.json`: Themenhäufigkeiten und Repräsentationen.
- `manifest.json`: Trainingsparameter, Seed, Paketversionen, Zeitstempel, Textspalten, Bereinigungseinstellungen und angewendete Ausreißerschwellwerte.

CSV-Dateien verwenden UTF-8 mit BOM. Der Export ist auch mit Pandas 1.5 kompatibel; ein Exportfehler unterbricht die Analyseansicht nicht mehr. Texte mit Formelpräfix werden für Tabellenkalkulationen mit einem Apostroph geschützt; JSON enthält die unveränderten Werte. Das Archiv enthält Texte aus dem Upload, aber weder die ursprüngliche Datei noch ausführbare Modellobjekte. Es dient der Ergebnisweitergabe, nicht dem Wiederaufnehmen des Trainings. Seed und Metadaten garantieren keine hardwareübergreifend identischen Ergebnisse.

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

Falls ein Traceback auf `/usr/local/anaconda3/lib/...` statt auf `.../envs/bertopic-dev/...` zeigt, läuft häufig noch die Conda-Basisumgebung. `conda activate bertopic-dev` ausführen und mit `python -m streamlit run app.py` starten, damit Streamlit denselben Python-Interpreter verwendet.

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

Die Tests benötigen keine heruntergeladenen Sprachmodelle. Sie prüfen Plotly-Kompatibilität, ausschließlich Ausreißer, kleine Datensätze, echtes BERTopic-Training mit synthetischen Embeddings, das Rendern aller drei Diagramme über Streamlit `AppTest`, erneute Seitenausführung sowie konsistentes Zurücksetzen von Ausreißern. Hinzu kommen Parameterprüfung vor dem Encoding, sichtbare und wechselbare Optionen im Modell-Dropdown, Modell-Prompts, der deaktivierte Trainingsbutton bei ungültigen Eingaben und der ZIP-/CSV-/JSON-Export. Die englische Stopwortliste des Testtrainings ist in scikit-learn enthalten. Der erste Lauf kann wegen der Numba-Kompilierung länger dauern.

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

## Optionale Themennamen mit OpenAI

Die App kann nach dem lokalen BERTopic-Training kurze Themennamen über die OpenAI-API erzeugen. **ChatGPT Pro beinhaltet keine API-Nutzung.** API-Key und Guthaben werden separat unter [OpenAI Platform](https://platform.openai.com/) verwaltet; Schlüssel lassen sich unter [API keys](https://platform.openai.com/api-keys) erstellen.

### API-Key auf deinem Mac hinterlegen

Im Projektverzeichnis die Datei `.streamlit/secrets.toml` mit deinem Editor anlegen:

```toml
OPENAI_API_KEY = "DEIN_NEUER_OPENAI_API_KEY"
```

Die Datei ist in `.gitignore` ausgeschlossen und darf nicht committed werden. Alternativ liest die App `OPENAI_API_KEY` oder `BERTOPIC_OPENAI_API_KEY` aus der Prozessumgebung. Die projektspezifische Variable hat Vorrang. Keine Schlüssel in Python-Dateien, Screenshots, Chat-Nachrichten oder Git speichern. Einen bereits geteilten Schlüssel widerrufen und ersetzen.

Streamlit danach vollständig neu starten, im aktivierten Conda-Environment:

```bash
conda activate bertopic-dev
python -m streamlit run app.py
```

In **Modellierung** steht **OpenAI-Verbindung** ganz oben in der Seitenleiste, vor den Modellparametern. Der Key-Status ist direkt sichtbar; Details und Modellkennung stehen unter **Einrichtung und Datenübertragung**. Dort die standardmäßig ausgeschaltete Checkbox **Themen mit OpenAI benennen (nur Keywords)** aktivieren. Ohne gefundenen Key ist sie ausgegraut. Das Modellfeld verwendet als Ausgangswert `gpt-4.1-mini`; eine andere für das Projekt verfügbare Responses-API-Modellkennung ist möglich. Key-Anwesenheit ist keine Prüfung seiner Gültigkeit oder des Guthabens. Solche Fehler werden beim tatsächlichen Benennen verständlich angezeigt, ohne das erfolgreiche BERTopic-Training zu verwerfen.

In **Analyse** ist die Benennung auch nachträglich möglich. Die Vorschau zeigt die Themen-IDs und Keywords, bevor **Keywords an OpenAI senden und Themen benennen** angeklickt wird. Ein gewöhnlicher UI-Rerun löst keinen neuen API-Aufruf aus. Ein erneuter Klick bzw. ein neues Training mit aktivierter Option kann erneut Kosten verursachen. Es gibt keine automatischen Wiederholungen fehlgeschlagener API-Aufrufe. Aufträge werden in Pakete mit maximal 20 Themen aufgeteilt; bei einem späteren Fehler können bereits Kosten entstanden sein, auch wenn keine neuen Namen übernommen werden.

### Welche Daten werden übertragen?

An `https://api.openai.com/v1/responses` gehen ausschließlich:

- bis zu zehn Keywords je Thema (jeweils maximal 80 Zeichen),
- die interne Themen-ID und die gewünschte Sprache,
- die Anweisung zur Benennung und das gewünschte Antwortschema.

Nicht übertragen werden Originaldatei, Original-/bereinigte Dokumenttexte, repräsentative Dokumentauszüge, Dokument-IDs, Dateinamen oder Embeddings. Ausreißer (`-1`) werden nicht benannt. **Keywords sind trotzdem aus den Daten abgeleitet und können Namen oder vertrauliche Begriffe enthalten.** Die Benennung ist daher kein vollständig lokaler Arbeitsschritt und keine automatische Anonymisierung.

Die API-Anfrage verwendet `store=false`. Das ist keine Zusage einer vollständigen Nullspeicherung: [Die Datenverwendungs- und Aufbewahrungsregeln der API](https://platform.openai.com/docs/guides/your-data) gelten weiterhin. Das lokale Programm übermittelt keinen Trainingsdatensatz zur Feinabstimmung, sondern einen Benennungsauftrag an ein bestehendes Modell.

Die Namen verändern weder Cluster noch Keywords. Sie erscheinen in der Themenübersicht, Diagrammbeschriftungen und CSV-/JSON-Exporten. Das Manifest dokumentiert Anbieter, Modell und den Keyword-Modus, niemals den API-Key. Nach Ausreißeränderungen werden Namen verworfen, damit alte Beschriftungen nicht versehentlich als aktuell gelten. Neue Namen lassen sich danach ausdrücklich erzeugen. Generierte Namen fachlich prüfen.

Die Anbindung nutzt den vorhandenen HTTP-Client `requests`, keinen zusätzlichen OpenAI-SDK. Die Tests simulieren API-Antworten und prüfen unter anderem den Datenumfang, deaktivierte Controls, Antwortvalidierung, Fehlersituationen, Benennung in den Diagrammen und das Vermeiden wiederholter Aufrufe. Ein bezahlter Live-Aufruf ist für die Tests weder nötig noch enthalten. In Cloud-Netzen muss `api.openai.com` für HTTPS erreichbar sein; Key-Werte gehören in die sicheren Umgebungs-/Secret-Einstellungen.
