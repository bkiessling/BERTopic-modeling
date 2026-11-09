# React-Workbench · #NDRfragt Topic Modeling

Die Anwendung besteht ausschließlich aus React/TypeScript und einem Python-/FastAPI-Backend. Die fachlichen BERTopic-Module wurden beibehalten; eine Streamlit-Oberfläche wird nicht mehr mitgeführt.

[Installation, Arbeitsablauf, Struktur, Tests und Konfiguration](../README.md)

## Design

- `#0C1754` als Hauptakzent, `#2671C6` für Hover/Fokus, `#FAFBFC` als heller Hintergrund.
- BERTopic im Header, „#NDRfragt Topic Modeling“ als Titel.
- Zentrierte Navigation Import · Modellierung · Ergebnisse, ohne Sidebar oder Footertext.
- Importfelder mit gleichen Höhen und Abständen: ID zuerst, dann durchsuchbares Textspalten-Multiselect ohne Vorauswahl.
- Gefilterte Originalvorschau vor der Bereinigung; danach direkt die bereinigten Texte und tatsächlichen IDs.
- Modellierung oben mit zwei schmaleren Kacheln um eine breitere Embedding-Auswahl; darunter drei Parameterkacheln.
- Aktionsbuttons ohne Icons, klare Hervorhebung und blaue Hover-Effekte.

![Import](screenshots/react-import.png)

![Modellierung](screenshots/react-modeling.png)

## Warum React?

Für den gewünschten kontrollierten Workflow mit Tabellen, Plotly und Hintergrundjobs passt React gut. Svelte wäre ebenfalls geeignet; es würde die Python-Modellierung nicht ersetzen. Die Trennung der Oberfläche von Training, Ergebniszustand, API und Jobverwaltung ist der entscheidende Architekturgewinn.
