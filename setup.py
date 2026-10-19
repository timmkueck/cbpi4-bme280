from setuptools import setup

setup(name='cbpi4-bme280',
      version='0.1.0',
      description='CraftBeerPi4: BME280 (Temperatur, Luftfeuchte, Luftdruck) über I²C',
      author='Timm Kück',
      url='https://github.com/timmkueck/cbpi4-bme280',
      include_package_data=True,
      package_data={'cbpi4_bme280': ['*.yaml', 'static/*']},
      packages=['cbpi4_bme280'],
      install_requires=['adafruit-circuitpython-bme280'],
      python_requires='>=3.9',
      )
