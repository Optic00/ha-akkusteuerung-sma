# Mitwirken

Beiträge sind willkommen. Arbeitssprache ist Deutsch.

## Vor dem Start

- Fehler, Fragen und Vorschläge über die
  [Issue-Vorlagen](https://github.com/Optic00/ha-opti-akkusteuerung/issues/new/choose)
  melden. Sicherheitslücken nach [SECURITY.md](SECURITY.md) privat melden.
- Vor größeren Änderungen, besonders an Strategie oder Schreibpfad, zuerst ein
  Issue eröffnen und den Ansatz abstimmen.

## Pull Requests

- Kleine, fokussierte Änderungen mit Tests. Einrichtung und alle Prüfungen stehen
  in [docs/development.md](docs/development.md).
- Strategieänderungen in `strategy/*.yaml` vornehmen und das erzeugte JSON
  mitcommitten.
- Hardwaretests ehrlich angeben: Was an welchem Gerät live geprüft wurde und was
  nur automatisiert. Zum Nachstellen keine Schreibfreigabe an einer produktiven
  Anlage einschalten.
- Keine privaten Daten ins Repository: keine Zugangsdaten, Hostnamen,
  Seriennummern, Shadow-Aufzeichnungen oder Messhistorien. Die CI prüft das
  zusätzlich.
- Beiträge stehen unter der [MIT-Lizenz](LICENSE) des Projekts.

Das unabhängige Review nach [REVIEW_POLICY.md](REVIEW_POLICY.md) führt der
Maintainer vor dem Merge durch. Externe Beitragende müssen dafür nichts
nachweisen. Wer KI-Werkzeuge genutzt hat, nennt sie bitte in der PR-Beschreibung.

## Umgang

Bleib sachlich und freundlich, auch bei Kritik. Keine privaten Daten anderer
veröffentlichen. Der Maintainer kann Beiträge, die dagegen verstoßen, ausblenden
oder schließen.
