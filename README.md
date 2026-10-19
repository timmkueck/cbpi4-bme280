# cbpi4-bme280

CraftBeerPi4-Sensor für den BME280 (Temperatur, Luftfeuchte, Luftdruck) über I²C.
Auf dem HAT „Biersteuerung“ steckt er an J3 (3,3 V).

Je Messwert legst du einen Sensor an (*Output type*: `temperature`, `humidity`, `pressure`).
Sensoren mit derselben Adresse teilen sich eine I²C-Verbindung und eine Messung.

## Installation

```bash
<python-von-craftbeerpi> -m pip install git+https://github.com/timmkueck/cbpi4-bme280@robust
```

Die Adafruit-Bibliothek wird mitinstalliert. I²C muss aktiv sein (`sudo raspi-config` → Interface → I2C).

## Einstellungen

| Eigenschaft | Vorgabe | Bedeutung |
|---|---|---|
| I2C Adresse | 118 (= 0x76) | 119 (= 0x77) bei geschlossener Lötbrücke; `0x77` als Text geht auch |
| Messintervall (s) | 2 | mindestens 1 |
| Output type | temperature | welcher Wert angezeigt wird |

## Änderungen gegenüber 0.0.1 (Zweig `robust`)

- Fehlt die Bibliothek oder antwortet der Sensor nicht, kommt eine **Meldung** in CraftBeerPi.
  Vorher blieb der Sensor still leer.
- Keine `print`-Ausgaben mehr (vorher drei Zeilen alle 2 s im Journal).
- Eine I²C-Verbindung je Adresse statt je Messwert. Gelesen wird in einem Thread, die Oberfläche hängt nicht.
- Nach einem Ausfall verbindet sich der Sensor selbst neu und meldet, wenn er wieder liefert.
- Paketordner heißt `cbpi4_bme280` (gültiger Python-Name). Der Sensortyp heißt weiter `BME280Sensor`,
  angelegte Sensoren bleiben gültig.

## Tests

```bash
pip install cbpi4 pytest
python -m pytest tests/ -q
```

Die Tests bilden die Adafruit-Bibliothek nach: drei Werte über eine Verbindung, fehlende Bibliothek, Ausfall und Erholung, Adressformate.
