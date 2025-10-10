# -*- coding: utf-8 -*-
import asyncio
import logging
import time
from cbpi.api import *

logger = logging.getLogger(__name__)

try:
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
except Exception as e:
    logger.error(f"[BME280Sensor] Bibliotheken fehlen: {e}")
    board = None
    busio = None
    adafruit_bme280 = None

@parameters([
    Property.Number(label="I2C Adresse", description="Adresse des BME280 Sensors (hex)", default_value=0x76),
    Property.Number(label="Messintervall (s)", description="Abtastrate für Messung & WebUI Update", default_value=2),
    Property.Select(
        label="Output type",
        options=["temperature", "humidity", "pressure"],
        description="Temperature, Humidity or pressure push to webinterface"
    )
])
class BME280Sensor(CBPiSensor):

    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.running = False
        self.temperature = 0.0
        self.humidity = 0.0
        self.pressure = 0.0
        self.interval = float(self.props.get("Messintervall (s)", 2))
        self.i2c_address = int(self.props.get("I2C Adresse", 0x76))
        self.bme280 = None
        logger.info("[BME280Sensor] Sensor instanziiert")

    async def start(self):
        await super().start()
        logger.info("[BME280Sensor] Start wird ausgeführt…")
        self.OutputType = str(self.props.get("Output type", "temperature"))
        self.running = True

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=self.i2c_address)
            logger.info(f"[BME280Sensor] Sensor initialisiert (Adresse: {hex(self.i2c_address)})")
        except Exception as e:
            logger.error(f"[BME280Sensor] Fehler beim Initialisieren des Sensors: {e}")
            self.running = False
            return

        asyncio.create_task(self.measure_and_push_loop())

    async def measure_and_push_loop(self):
        """Async-Messloop für Temperatur, Luftfeuchtigkeit und Luftdruck"""
        logger.info("[BME280Sensor] Async-Messloop gestartet")
        while self.running:
            try:
                self.temperature = self.bme280.temperature
                self.humidity = self.bme280.humidity
                self.pressure = self.bme280.pressure

                print(self.temperature)
                print(self.humidity)
                print(self.pressure)

                # Wert basierend auf OutputType auswählen
                if self.OutputType == "temperature":
                    self.value = self.temperature
                elif self.OutputType == "humidity":
                    self.value = self.humidity
                elif self.OutputType == "pressure":
                    self.value = self.pressure
                self.push_update(self.value)
                self.log_data(self.value)

                logger.debug(f"[BME280Sensor] T={self.temperature:.2f}°C, H={self.humidity:.2f}%, P={self.pressure:.2f} hPa")
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"[BME280Sensor] Fehler im Messloop: {e}")
                await asyncio.sleep(1)
        logger.info("[BME280Sensor] Messloop beendet")

    async def stop(self):
        logger.info("[BME280Sensor] Stop wird ausgeführt…")
        self.running = False
        await asyncio.sleep(0.1)
        await super().stop()
        logger.info("[BME280Sensor] Sensor gestoppt")

def setup(cbpi):
    cbpi.plugin.register("BME280Sensor", BME280Sensor)
    logger.info("[BME280Sensor] Plugin registriert")
