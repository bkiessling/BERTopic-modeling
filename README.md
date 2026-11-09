# Topic Modeling mit BERTopic

Interaktive Streamlit-Anwendung für explorative Themenanalysen deutscher und englischer Texte. CSV- und Excel-Dateien werden hochgeladen, bereinigt, mit BERTopic modelliert und anschließend als Tabellen und Plotly-Diagramme untersucht.

## Installation

Getestet mit Python 3.12. Eine virtuelle Umgebung wird empfohlen:

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

Neue bereinigte Daten verwerfen das bisherige Modell der Sitzung. Ein Browser-Neustart bzw. eine neue Streamlit-Sitzung kann Ergebnisse verlieren; ein persistenter Modell- und Ergebnisexport ist derzeit nicht implementiert.

### Netzwerk und Modelle

Pakete kommen von PyPI und gegebenenfalls `download.pytorch.org`. NLTK lädt Stopwörter von `raw.githubusercontent.com`. Die Embedding-Modelle werden bei erster Verwendung von Hugging Face heruntergeladen und lokal zwischengespeichert. Öffentliche Modelle benötigen grundsätzlich keinen API-Key.

In eingeschränkten Cloud-Netzen müssen `huggingface.co` und die tatsächlichen Download-/Redirect-Ziele zugelassen sein, gegebenenfalls `*.huggingface.co` sowie die verwendeten Xet-CDN-Hosts. In der aktuellen Cloud-Umgebung war Hugging Face beim Prüfen mit HTTP 403 blockiert. Die Tests nutzen deshalb lokale synthetische Embeddings; Modell-Downloads und die semantische Qualität der realen Embeddings wurden damit nicht geprüft.

Das optionale Jina-Modell verwendet `trust_remote_code=True` und führt Modellcode aus dem heruntergeladenen Repository aus. Vor produktivem Einsatz Modellrevisionen prüfen und festlegen.

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

Die Tests benötigen keine heruntergeladenen Sprachmodelle. Sie prüfen Plotly-Kompatibilität, ausschließlich Ausreißer, kleine Datensätze, echtes BERTopic-Training mit synthetischen Embeddings, das Rendern aller drei Diagramme über Streamlit `AppTest`, erneute Seitenausführung sowie konsistentes Zurücksetzen von Ausreißern. Die englische Stopwortliste des Testtrainings ist in scikit-learn enthalten. Der erste Lauf kann wegen der Numba-Kompilierung länger dauern.

## Repository-Struktur

```text
app.py                      Streamlit-Einstieg und Weiterleitung
pages/                      Upload, Modellierung und Analyse
modules/
  upload/                   Dateiformate und CSV-Trennzeichen
  preprocessing/            Textauswahl, Bereinigung und Stopwörter
  modeling/                 Parameter-Widgets und BERTopic-Training
  analysis/                 Ergebnistabellen und Ausreißerbehandlung
  viz/                      Diagramme und gecachte Projektion
  ui/                       Erläuterungen
assets/                     Logo
.streamlit/config.toml      Darstellung und Streamlit-Einstellungen
tests/                      Regressionstests und Streamlit-Integration
requirements.txt            Getestete direkte Python-Abhängigkeiten
```

Die Trennung nach Arbeitsschritten ist für die aktuelle Größe sinnvoll. UI und Trainingslogik sind noch teilweise gekoppelt (`st.session_state` im Training). `topic_modeling.py` ist ein älterer Einstieg; unterstützt wird `app.py`. `modules/viz/heatmap.py` enthält eine weitere, derzeit nicht eingebundene Wortgewichtungsansicht.

## Eignung und nächste Schritte

Streamlit eignet sich für explorative Analysen, interne Fachanwendungen und einen kleinen Nutzerkreis. Eine Migration ist dafür nicht nötig. Für lange, parallele Trainingsjobs und einen öffentlich betriebenen Mehrbenutzerdienst fehlen derzeit Hintergrundjobs, persistente Ergebnisse, Fortschritts-/Fehlerverwaltung außerhalb der Browser-Sitzung und ein Betriebskonzept für Authentifizierung und Ressourcenlimits.

Prioritäten für die weitere Entwicklung:

- Trainingslogik von Widgets und `session_state` trennen; ein gemeinsames Modell für Konfiguration und Ergebnisse einführen.
- Sprachmodell und Sprache fachlich aufeinander abstimmen; englische Modelle nicht pauschal für deutsche Texte empfehlen. Automatische Modellwahl anhand der Textlänge allein ist nicht belastbar.
- Parameter vor dem Training auf Datensatzgröße abstimmen und Qualitätsmaße sowie nachvollziehbare Modellmetadaten ergänzen.
- Fehlgeschlagene Uploads mit verständlichen Meldungen behandeln, Zeichencodierung und Datenqualität prüfen.
- Modell-/Ergebnisexport, vollständiges Lockfile und CI ergänzen; ungenutzte Einstiege und Module anschließend konsolidieren.
- Bei großen Datenmengen Projektionen begrenzen bzw. gezielt berechnen und Training in einen Hintergrundprozess auslagern.
