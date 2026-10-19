# -*- coding: utf-8 -*-
"""CraftBeerPi4-Sensor fuer den BME280 (Temperatur, Luftfeuchte, Luftdruck).

Mehrere Sensoren (je ein Messwert) mit derselben Adresse teilen sich eine
I2C-Verbindung und eine Messung. Gelesen wird in einem Thread, damit die
asyncio-Schleife von CraftBeerPi nicht blockiert. Fehlt eine Bibliothek oder
antwortet der Sensor nicht, gibt es eine Meldung -- keinen still leeren Wert.
"""
import asyncio
import logging
import threading
import time

from cbpi.api import CBPiSensor, Property, parameters
from cbpi.api.dataclasses import NotificationType

logger = logging.getLogger(__name__)

try:
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    IMPORTFEHLER = None
except Exception as e:  # Bibliothek fehlt oder keine I2C-Hardware
    board = busio = adafruit_bme280 = None
    IMPORTFEHLER = str(e)

WERTE = {"temperature": ("temperature", "°C"), "humidity": ("humidity", "%"), "pressure": ("pressure", "hPa")}


class Messstelle:
    """Eine I2C-Verbindung je Adresse, Messung hoechstens alle `min_abstand` s."""

    _alle = {}
    _lock = threading.Lock()

    @classmethod
    def holen(cls, adresse):
        with cls._lock:
            if adresse not in cls._alle:
                cls._alle[adresse] = cls(adresse)
            return cls._alle[adresse]

    def __init__(self, adresse, min_abstand=1.0):
        self.adresse = adresse
        self.min_abstand = min_abstand
        self.geraet = None
        self.werte = None
        self.zeit = 0.0
        self.lock = threading.Lock()

    def messen(self):
        """Dict mit temperature/humidity/pressure; wirft bei Fehler."""
        with self.lock:
            if self.werte is not None and time.monotonic() - self.zeit < self.min_abstand:
                return self.werte
            if IMPORTFEHLER:
                raise RuntimeError(f"Bibliothek fehlt: {IMPORTFEHLER}")
            try:
                if self.geraet is None:
                    i2c = busio.I2C(board.SCL, board.SDA)
                    self.geraet = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=self.adresse)
                self.werte = {"temperature": float(self.geraet.temperature),
                              "humidity": float(self.geraet.humidity),
                              "pressure": float(self.geraet.pressure)}
            except Exception:
                self.geraet = None  # beim naechsten Mal neu verbinden
                self.werte = None
                raise
            self.zeit = time.monotonic()
            return self.werte


def adresse_lesen(wert, vorgabe=0x76):
    """Nimmt 118, "118", "0x76" oder "76" (hex) an."""
    if wert in (None, ""):
        return vorgabe
    if isinstance(wert, (int, float)):
        return int(wert)
    text = str(wert).strip().lower()
    if text.startswith("0x"):
        return int(text, 16)
    zahl = int(text)
    return int(text, 16) if zahl in (76, 77) else zahl


@parameters([
    Property.Number(label="I2C Adresse", configurable=True, default_value=0x76,
                    description="118 (0x76) oder 119 (0x77)"),
    Property.Number(label="Messintervall (s)", configurable=True, default_value=2,
                    description="Abtastrate für Messung und Anzeige"),
    Property.Select(label="Output type", options=["temperature", "humidity", "pressure"],
                    description="Welcher Messwert angezeigt wird"),
])
class BME280Sensor(CBPiSensor):

    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.value = None
        self.zeit = None
        self.fehler = ""

    def alter(self):
        return None if self.zeit is None else time.monotonic() - self.zeit

    async def run(self):
        intervall = max(1.0, float(self.props.get("Messintervall (s)", 2) or 2))
        art = str(self.props.get("Output type", "temperature") or "temperature")
        try:
            stelle = Messstelle.holen(adresse_lesen(self.props.get("I2C Adresse")))
        except ValueError as e:
            stelle = None
            self._fehler(f"Ungültige I2C-Adresse: {e}")
        while self.running and stelle is not None:
            try:
                werte = await asyncio.to_thread(stelle.messen)
                self.value = round(werte[WERTE.get(art, WERTE["temperature"])[0]], 2)
                self.zeit = time.monotonic()
                self.push_update(self.value)
                self.log_data(self.value)
                if self.fehler:
                    self.fehler = ""
                    self.cbpi.notify("BME280", f"Sensor liefert wieder ({art})", NotificationType.SUCCESS)
                logger.debug("BME280 %s: %s", art, werte)
            except Exception as e:
                self._fehler(f"Adresse {hex(stelle.adresse)}: {e}")
            await asyncio.sleep(intervall)

    def _fehler(self, text):
        if text != self.fehler:
            self.fehler = text
            logger.error("BME280: %s", text)
            self.cbpi.notify("BME280", text, NotificationType.ERROR)

    def get_state(self):
        return dict(value=self.value)

    def get_unit(self):
        return WERTE.get(str(self.props.get("Output type", "temperature")), WERTE["temperature"])[1]


def setup(cbpi):
    cbpi.plugin.register("BME280Sensor", BME280Sensor)
    if IMPORTFEHLER:
        logger.error("BME280: Bibliothek fehlt (%s). pip install adafruit-circuitpython-bme280", IMPORTFEHLER)
