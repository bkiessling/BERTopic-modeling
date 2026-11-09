# Embedding-Modelle für deutsche Themenanalysen

## Einordnung der vom Nutzer gezeigten MTEB(deu, v1)-Ergebnisse

Der bereitgestellte Ausschnitt enthält sechs Modelle von insgesamt 114. Er ist kein vollständiger Nachweis des aktuellen Clustering-Spitzenplatzes. Für BERTopic ist die Spalte **Clust.** besonders relevant; der Gesamtmittelwert mischt sechs unterschiedliche Aufgabentypen.

| Modell | Parameter | Mean (Task) | Clust. |
| --- | ---: | ---: | ---: |
| codefuse-ai/F2LLM-v2-14B | 14,0 Mrd. | 67,02 | 45,71 |
| codefuse-ai/F2LLM-v2-8B | 7,6 Mrd. | 66,81 | 45,49 |
| codefuse-ai/F2LLM-v2-4B | 4,0 Mrd. | 66,06 | 43,68 |
| jinaai/jina-embeddings-v5-text-nano | 212 Mio. | 64,76 | 41,00 |
| codefuse-ai/F2LLM-v2-1.7B | 1,7 Mrd. | 65,08 | 41,68 |

**Benchmark-Ergebnis:** Unter den gezeigten Modellen führt F2LLM-v2-14B beim Gesamtmittel und beim Clustering. Die 8B-Variante liegt im Clustering nur 0,22 Punkte dahinter. Andere Modelle außerhalb des Ausschnitts könnten bei einzelnen Aufgabentypen besser abschneiden.

**Intel-Mac:** Jina v5 text nano ist wegen seiner 212 Mio. Parameter ein interessanter Effizienzkandidat. Das 1,7B-F2LLM hat ungefähr achtmal so viele Parameter und liegt im gezeigten Clustering-Wert nur 0,68 Punkte darüber. Daraus folgt keine Garantie für den eigenen Datensatz. Große 8B-/14B-Modelle sind für lokale CPU-Analysen auf einem gewöhnlichen Intel-Mac keine sinnvolle Standardwahl.

Die Jina-/F2LLM-Modellkarten konnten in dieser Cloud wegen der gesperrten Hugging-Face-Verbindung nicht geprüft werden. Diese Modelle werden deshalb nicht als bereits verifizierte Ladeoptionen angeboten. Insbesondere Prompt, Pooling, Modellarchitektur und notwendige Zusatzpakete müssen vor einer Integration geklärt werden. Die im Ausschnitt fehlende Zero-shot-Angabe für Jina bedeutet fehlende Vergleichsinformation; daraus lässt sich keine Datenkontamination ableiten.

## Auswahl in der App

Für Deutsch stehen sechs Optionen zur Verfügung. Pro Training wird genau ein Modell verwendet; die Zahl der Optionen erscheint unter dem Dropdown.

| Modell | Verwendung | Aufwand / Einschränkung |
| --- | --- | --- |
| [Multilingual MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) | Schnelle Ausgangsbasis | Älter, kein beanspruchter State-of-the-Art |
| [Multilingual MPNet](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2) | Größere Alternative | Mehr Rechenaufwand als MiniLM |
| [Multilingual E5 small](https://huggingface.co/intfloat/multilingual-e5-small) | Kompakter Kandidat für Intel-CPU | `query: ` wird automatisch vorangestellt |
| [Multilingual E5 base](https://huggingface.co/intfloat/multilingual-e5-base) | Größerer E5-Vergleichskandidat | Gleicher automatischer Präfix |
| [BGE-M3](https://huggingface.co/BAAI/bge-m3) | Mehrsprachige, auch lange Texte | Hoher RAM-Bedarf; nur dichte Vektoren werden verwendet |
| [Qwen3 Embedding 0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | Moderner, experimenteller Vergleich | Auf CPU aufwendig; automatische Clustering-Instruktion |

Für den Intel-Mac zunächst MiniLM oder E5 small verwenden, danach E5 base mit denselben Texten vergleichen. Die Auswahl ist eine praktische Kandidatenliste, keine Rangliste. Sie sagt nicht voraus, welches Modell auf dem eigenen Korpus die besten Themen liefert. Bei langen Texten die Tokenlimits beachten; lange BGE-/Qwen-Eingaben können trotz kleiner Batches sehr viel Speicher benötigen.

Prompts werden am Encoder hinterlegt, damit Dokumente und die von BERTopic für Themenrepräsentationen eingebetteten Texte konsistent behandelt werden. Prompt und Batchgröße werden im Ergebnismanifest dokumentiert. Für BGE-M3 und Qwen werden kleinere Batches verwendet. Die ursprünglichen bereinigten Texte bleiben im Ergebnisexport ohne angefügten Prompt erhalten.

## Quellen und Verifikationsgrenzen

Direkte Hugging-Face-Abfragen lieferten in der Cloud HTTP 403. Folgende offizielle Entwicklerquellen waren zugänglich:

- [Qwen3 Embedding – offizielles Repository](https://github.com/QwenLM/Qwen3-Embedding): mehrsprachig einschließlich Deutsch, Sentence-Transformers-Nutzung und Instruktionen. Die dortige Behauptung des ersten Platzes für 8B bezieht sich auf den **5. Juni 2025**, nicht auf einen aktuell geprüften deutschen Spitzenplatz.
- [BGE-M3 – offizielle Dokumentation](https://github.com/FlagOpen/FlagEmbedding/tree/master/research/BGE_M3): über 100 Sprachen, bis zu 8192 Tokens, 1024-dimensionale dichte Vektoren sowie zusätzliche Retrieval-Modi.
- [Multilingual E5 – offizielles Repository](https://github.com/microsoft/unilm/tree/master/e5) und [Evaluationscode](https://github.com/microsoft/unilm/blob/master/e5/mteb_except_retrieval_eval.py): mehrsprachige Modellgrößen und Verwendung von `query: ` für die hier relevanten Nicht-Retrieval-Aufgaben.

Tests prüfen Dropdown-Wechsel, Prompt-Konfiguration und kleine lokal erzeugte BERT-/Qwen3-Modelle einschließlich Safetensors-Laden und Encoding. Die ursprünglichen Modellgewichte konnten wegen der Netzsperre nicht heruntergeladen werden; ihre Ladefähigkeit und die Qualität der resultierenden Themen werden damit nicht als geprüft behauptet.
