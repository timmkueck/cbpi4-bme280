# CLAUDE.md – cbpi4-bme280

Gilt zusätzlich zur übergeordneten `~/Claude/CLAUDE.md`. CraftBeerPi4-Sensor für den BME280 am Brau-Pi
(HAT „Biersteuerung“, J3). Teil des Brau-Verbunds, Gesamtbild in `Biersteuerung/docs/systeme.md`.

- `master`: Stand 0.0.1 (still leer bei Fehlern, `print`-Ausgaben). Zweig **`robust`**: 0.1.0. Nicht ungefragt mergen.
- Paketordner `cbpi4_bme280`, Sensortyp `BME280Sensor` (nicht umbenennen, sonst sind angelegte Sensoren ungültig).
- Fehler immer melden (`cbpi.notify`), nie still `None`. Eine I²C-Verbindung je Adresse (`Messstelle`), Lesen im Thread.
- Tests ohne Hardware: `pip install cbpi4 pytest && python -m pytest tests/ -q` (Adafruit-Bibliothek nachgebildet).
- Wird mit der Brauzentrale (Phase 3+) eventuell durch den Boten ersetzt, siehe `Biersteuerung/docs/zentrale.md`.
