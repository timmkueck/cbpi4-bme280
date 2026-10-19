"""Tests ohne Hardware (nachgebildete Adafruit-Bibliothek):
pip install cbpi4 pytest && python -m pytest tests/ -q"""
import asyncio
import importlib
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("cbpi")
from cbpi.api.dataclasses import Props  # noqa: E402


class FakeBME:
    verbindungen = 0
    messungen = 0
    kaputt = False

    def __init__(self, i2c, address):
        FakeBME.verbindungen += 1
        self.address = address

    def _wert(self, w):
        if FakeBME.kaputt:
            raise OSError("Remote I/O error")
        FakeBME.messungen += 1
        return w

    @property
    def temperature(self):
        return self._wert(21.5)

    @property
    def humidity(self):
        return 48.25

    @property
    def pressure(self):
        return 1013.2


def laden(mit_bibliothek=True):
    for name in ("board", "busio", "adafruit_bme280", "adafruit_bme280.basic", "cbpi4_bme280"):
        sys.modules.pop(name, None)
    if mit_bibliothek:
        sys.modules["board"] = types.SimpleNamespace(SCL=3, SDA=2)
        sys.modules["busio"] = types.SimpleNamespace(I2C=lambda scl, sda: object())
        basic = types.SimpleNamespace(Adafruit_BME280_I2C=FakeBME)
        sys.modules["adafruit_bme280"] = types.SimpleNamespace(basic=basic)
        sys.modules["adafruit_bme280.basic"] = basic
    else:
        sys.modules["board"] = None
    FakeBME.verbindungen = FakeBME.messungen = 0
    FakeBME.kaputt = False
    return importlib.import_module("cbpi4_bme280")


class FakeCbpi:
    def __init__(self):
        self.notes, self.registered = [], {}
        self.log = types.SimpleNamespace(log_data=lambda id, v: None)
        self.ws = types.SimpleNamespace(send=lambda d, s=False: None)
        self.plugin = types.SimpleNamespace(register=lambda n, c: self.registered.__setitem__(n, c))

    def push_update(self, *a, **k):
        pass

    def notify(self, title, message, type=None, action=[]):
        self.notes.append((title, message, type))


async def laufen(sensoren, sekunden):
    for s in sensoren:
        s.running = True
    tasks = [asyncio.create_task(s.run()) for s in sensoren]
    await asyncio.sleep(sekunden)
    for s in sensoren:
        s.running = False
    await asyncio.gather(*tasks)


def test_drei_werte_eine_verbindung():
    m = laden()
    c = FakeCbpi()
    m.setup(c)
    assert "BME280Sensor" in c.registered
    s = [m.BME280Sensor(c, f"s{i}", Props({"I2C Adresse": 118, "Messintervall (s)": 1, "Output type": art}))
         for i, art in enumerate(["temperature", "humidity", "pressure"])]
    asyncio.run(laufen(s, 0.5))
    assert [x.value for x in s] == [21.5, 48.25, 1013.2]
    assert [x.get_unit() for x in s] == ["°C", "%", "hPa"]
    assert FakeBME.verbindungen == 1 and FakeBME.messungen == 1
    assert c.notes == []


def test_fehlende_bibliothek_wird_gemeldet():
    m = laden(mit_bibliothek=False)
    c = FakeCbpi()
    s = m.BME280Sensor(c, "s", Props({"Output type": "temperature"}))
    asyncio.run(laufen([s], 0.3))
    assert s.value is None and any("Bibliothek fehlt" in n[1] for n in c.notes)


def test_ausfall_meldet_einmal_und_erholt_sich():
    m = laden()
    c = FakeCbpi()
    s = m.BME280Sensor(c, "s", Props({"I2C Adresse": "0x77", "Messintervall (s)": 1}))

    async def go():
        s.running = True
        t = asyncio.create_task(s.run())
        await asyncio.sleep(0.3)
        FakeBME.kaputt = True
        await asyncio.sleep(2.5)
        alt = s.alter()
        FakeBME.kaputt = False
        await asyncio.sleep(1.5)
        s.running = False
        await t
        return alt
    alt = asyncio.run(go())
    fehler = [n for n in c.notes if "Remote I/O" in n[1]]
    assert len(fehler) == 1 and "0x77" in fehler[0][1]
    assert alt > 1.5 and s.alter() < 1.5
    assert any("wieder" in n[1] for n in c.notes)


@pytest.mark.parametrize("ein,aus", [(118, 0x76), (118.0, 0x76), ("0x77", 0x77), ("76", 0x76), (None, 0x76)])
def test_adresse(ein, aus):
    m = laden()
    assert m.adresse_lesen(ein) == aus
