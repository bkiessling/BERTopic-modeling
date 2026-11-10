# React-Workbench · #NDRfragt Themenfinder

Die Anwendung besteht ausschließlich aus React/TypeScript und einem Python-/FastAPI-Backend. Die fachlichen BERTopic-Module wurden beibehalten; eine Streamlit-Oberfläche wird nicht mehr mitgeführt.

[Installation, Arbeitsablauf, Struktur, Tests und Konfiguration](../README.md)

## Design

- `#0C1754` als Hauptakzent, `#2671C6` für Hover/Fokus, `#FAFBFC` als heller Hintergrund.
- Topic Modeling im Header, „#NDRfragt Themenfinder“ als Titel.
- Zentrierte Navigation Import · Modellierung · Ergebnisse, ohne Sidebar oder Footertext.
- Importfelder mit gleichen Höhen und Abständen: ID zuerst, dann durchsuchbares Textspalten-Multiselect ohne Vorauswahl.
- Gefilterte Originalvorschau vor der Bereinigung; danach direkt die bereinigten Texte und tatsächlichen IDs.
- Modellierung oben mit zwei schmaleren Kacheln um eine breitere Embedding-Auswahl; darunter drei Parameterkacheln.
- Aktionsbuttons ohne Icons, klare Hervorhebung und blaue Hover-Effekte.

![Import](screenshots/react-import.png)

![Modellierung](screenshots/react-modeling.png)

## Warum React?

Für den gewünschten kontrollierten Workflow mit Tabellen, Plotly und Hintergrundjobs passt React gut. Svelte wäre ebenfalls geeignet; es würde die Python-Modellierung nicht ersetzen. Die Trennung der Oberfläche von Training, Ergebniszustand, API und Jobverwaltung ist der entscheidende Architekturgewinn.

## Ergebnisansicht

Zwei Ansichten: Themenübersicht und Visualisierungen. Die Textbeiträge bleiben darunter sichtbar und bieten Suche, Themenfilter, Sortierung über Spaltenüberschriften. „Ergebnisse verbessern“ steht oberhalb der Ansicht; Trainingsparameter sind über das kleine Symbol am Ergebnis-Titel erreichbar.

Visualisierungen starten mit dem höheren Netzwerk. Top-Keywords bietet ein durchsuchbares Multiselect für bis zu vier Themen und einen Regler für die Keyword-Anzahl (begrenzt durch die beim Training gespeicherten Keywords). Die Balken verwenden `#0C1754`.

Die Importvorschau zeigt unmittelbar nach Upload drei Originalzeilen aller Spalten; nach Bereinigung wird ausschließlich die bereinigte Vorschau angezeigt. API-Keys können beim Einschalten der Benennung im Dialog für den aktuellen Arbeitsbereich hinterlegt werden.

Die Hilfe-Texte sind zentral in `src/content/help.de.json` konfigurierbar. Voreinstellungen erklärt die Heuristiken; der Reset ist ein ausgeschriebener Button. Ergebnisansichten verwenden „Thema“ als erste und „Themenname“ als zweite Spalte und denselben Namen in Filtern und Diagrammen.

„Ergebnisse verbessern“ bietet neben Outlier-Zuordnung die Reduktion ähnlicher Themen. Zielanzahlen schließen Outlier aus. Nach Strukturänderungen lassen sich Namen in der kompakten Sektion „Themen neu benennen“ aktualisieren.

Die Analyse-Tabs stehen direkt unter der Hauptnavigation, zentriert mit eigenen Icons. Unter „Ergebnisse verbessern“ können ausgewählte Themen gezielt zusammengeführt und Themennamen ohne API bearbeitet werden. Andere Namen überstehen das Umnummerieren von Themen-IDs bei einer Zusammenführung. Manuelle Namen übersteuern KI-Namen. Outlier behalten zwingend ihren festen Namen; eine zentrale Hilfe erklärt sie.

Die Verbesserungsaktionen bilden ein Raster aus zwei Spalten und drei Reihen, mit ausgerichteten Aktionsleisten. Themen lassen sich reversibel aus der Auswertung ausschließen; Tabellen, Kennzahlen, Diagramme und Export berücksichtigen dieselbe Auswahl. Strukturänderungen erfordern zuvor „Alle wieder einblenden“. Die Netzwerkfarben werden pro Themen-ID zugeordnet; Outlier sind grau.
