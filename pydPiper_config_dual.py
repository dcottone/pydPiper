import logging
import sys
if sys.version_info[0] < 3:
    import ConfigParser
    config = ConfigParser.RawConfigParser()
else:
    import configparser
    config = configparser.RawConfigParser()

config.read('pydPiper_dual.cfg')

def safeget(config, section, option, default=None):
    return config.has_option(section, option) and config.get(section, option) or default

# Start-up mode
STARTUP_MSG_DURATION = float(safeget(config,'STARTUP', 'startup_msg_duration',0))

# Display 1 Parameters
DISPLAY_1_DRIVER= safeget(config,'DISPLAY_1', 'display_driver')
DISPLAY_1_DEVICETYPE= safeget(config,'DISPLAY_1', 'display_devicetype')
DISPLAY_1_WIDTH = int(safeget(config,'DISPLAY_1', 'display_width',0)) # the  width of the display in pixels
DISPLAY_1_HEIGHT = int(safeget(config,'DISPLAY_1', 'display_height',0)) # the height of the display in pixels
DISPLAY_1_SIZE = (DISPLAY_1_WIDTH, DISPLAY_1_HEIGHT)
DISPLAY_1_PIN_RS = int(safeget(config,'DISPLAY_1', 'display_pin_rs',0))
DISPLAY_1_PIN_E = int(safeget(config,'DISPLAY_1', 'display_pin_e',0))
DISPLAY_1_PIN_D4 = int(safeget(config,'DISPLAY_1', 'display_pin_d4',0))
DISPLAY_1_PIN_D5 = int(safeget(config,'DISPLAY_1', 'display_pin_d5',0))
DISPLAY_1_PIN_D6 = int(safeget(config,'DISPLAY_1', 'display_pin_d6',0))
DISPLAY_1_PIN_D7 = int(safeget(config,'DISPLAY_1', 'display_pin_d7',0))
DISPLAY_1_PINS_DATA = [ DISPLAY_1_PIN_D4, DISPLAY_1_PIN_D5, DISPLAY_1_PIN_D6, DISPLAY_1_PIN_D7 ]
i2c_address_1 = safeget(config,'DISPLAY_1', 'display_i2c_address','0')
DISPLAY_1_I2C_ADDRESS = int(i2c_address_1) if i2c_address_1 and 'x' not in i2c_address_1 else int(i2c_address_1,16)
DISPLAY_1_I2C_PORT = int(safeget(config,'DISPLAY_1', 'display_i2c_port',0))
DISPLAY_1_ENABLE_DURATION = float(safeget(config,'DISPLAY_1', 'display_enable_duration',0)) # in microseconds.  Decrease to increase performance.  Increase to improve display stability

DISPLAY_1_SPI_DEVICE = int(safeget(config,'DISPLAY_1', 'display_spi_device',0))
DISPLAY_1_SPI_PORT = int(safeget(config,'DISPLAY_1', 'display_spi_port',0))
DISPLAY_1_GPIO_DC = int(safeget(config,'DISPLAY_1', 'display_gpio_dc',0))
DISPLAY_1_GPIO_RST = int(safeget(config,'DISPLAY_1', 'display_gpio_rst',0))

# Page Parameters
PAGEFILE_1 = safeget(config, 'DISPLAY_1', 'pagefile')
ANIMATION_SMOOTHING_1 = float(safeget(config,'DISPLAY_1', 'animation_smoothing',0)) # Amount of time in seconds to wait before repainting display

# Display 2 Parameters
DISPLAY_2_DRIVER= safeget(config,'DISPLAY_1', 'display_driver')
DISPLAY_2_DEVICETYPE= safeget(config,'DISPLAY_1', 'display_devicetype')
DISPLAY_2_WIDTH = int(safeget(config,'DISPLAY_1', 'display_width',0)) # the  width of the display in pixels
DISPLAY_2_HEIGHT = int(safeget(config,'DISPLAY_1', 'display_height',0)) # the height of the display in pixels
DISPLAY_2_SIZE = (DISPLAY_2_WIDTH, DISPLAY_2_HEIGHT)
DISPLAY_2_PIN_RS = int(safeget(config,'DISPLAY_2', 'display_pin_rs',0))
DISPLAY_2_PIN_E = int(safeget(config,'DISPLAY_2', 'display_pin_e',0))
DISPLAY_2_PIN_D4 = int(safeget(config,'DISPLAY_2', 'display_pin_d4',0))
DISPLAY_2_PIN_D5 = int(safeget(config,'DISPLAY_2', 'display_pin_d5',0))
DISPLAY_2_PIN_D6 = int(safeget(config,'DISPLAY_2', 'display_pin_d6',0))
DISPLAY_2_PIN_D7 = int(safeget(config,'DISPLAY_2', 'display_pin_d7',0))
DISPLAY_2_PINS_DATA = [ DISPLAY_2_PIN_D4, DISPLAY_2_PIN_D5, DISPLAY_2_PIN_D6, DISPLAY_2_PIN_D7 ]
i2c_address_2 = safeget(config,'DISPLAY_2', 'display_i2c_address','0')
DISPLAY_2_I2C_ADDRESS = int(i2c_address_2) if i2c_address_2 and 'x' not in i2c_address_2 else int(i2c_address_2,16)
DISPLAY_2_I2C_PORT = int(safeget(config,'DISPLAY_2', 'display_i2c_port',0))
DISPLAY_2_ENABLE_DURATION = float(safeget(config,'DISPLAY_2', 'display_enable_duration',0)) # in microseconds.  Decrease to increase performance.  Increase to improve display stability

DISPLAY_2_SPI_DEVICE = int(safeget(config,'DISPLAY_2', 'display_spi_device',0))
DISPLAY_2_SPI_PORT = int(safeget(config,'DISPLAY_2', 'display_spi_port',0))
DISPLAY_2_GPIO_DC = int(safeget(config,'DISPLAY_2', 'display_gpio_dc',0))
DISPLAY_2_GPIO_RST = int(safeget(config,'DISPLAY_2', 'display_gpio_rst',0))

# Page Parameters
PAGEFILE_2 = safeget(config, 'DISPLAY_2', 'pagefile')
ANIMATION_SMOOTHING_2 = float(safeget(config,'DISPLAY_2', 'animation_smoothing',0)) # Amount of time in seconds to wait before repainting display


# System Parameters
# This is where the log file will be written
LOGFILE=safeget(config,'SYSTEM','logfile')

# Logging level
LOGLEVEL={'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'critical': logging.CRITICAL }.get(safeget(config,'SYSTEM', 'loglevel'))

# Localization Parameters
# Adjust this setting to localize the time display to your region
TIMEZONE=safeget(config,'SYSTEM', 'timezone')
TIME24HOUR=bool(safeget(config, 'SYSTEM', 'time24hour',False))

# Adjust this setting to localize temperature displays
TEMPERATURE=safeget(config,'SYSTEM', 'temperature')

# Weather related variables
WEATHER_SERVICE = safeget(config,'SYSTEM', 'weather_service')
WEATHER_API = safeget(config,'SYSTEM', 'weather_api')
WEATHER_LOCATION = safeget(config,'SYSTEM', 'weather_location')


# Music Source Parameters
MUSIC_SERVICE = safeget(config, 'SOURCE', 'source_type')

# Used by Volumio V1 and Moode
MPD_SERVER = safeget(config, 'SOURCE', 'mpd_server')
MPD_PORT = safeget(config, 'SOURCE', 'mpd_port')
MPD_PASSWORD = safeget(config, 'SOURCE', 'mpd_password')

# Used by Volumio v1 and Moode
SPOP_SERVER = safeget(config, 'SOURCE', 'spop_server')
SPOP_PORT = safeget(config, 'SOURCE', 'spop_port')
SPOP_PASSWORD = safeget(config, 'SOURCE', 'spop_password')

# Used by Volumio v2
VOLUMIO_SERVER = safeget(config, 'SOURCE', 'volumio_server')
VOLUMIO_PORT = safeget(config, 'SOURCE', 'volumio_port')

# Used by RuneAudio
RUNE_SERVER = safeget(config, 'SOURCE', 'rune_server')
RUNE_PORT = safeget(config, 'SOURCE', 'rune_port')
RUNE_PASSWORD = safeget(config, 'SOURCE', 'rune_password')

# Used by Max2Play and piCorePlayer
LMS_SERVER = safeget(config, 'SOURCE', 'lms_server')
LMS_PORT = safeget(config, 'SOURCE', 'lms_port')
LMS_USER = safeget(config, 'SOURCE', 'lms_user')
LMS_PASSWORD = safeget(config, 'SOURCE', 'lms_password')
LMS_PLAYER = safeget(config, 'SOURCE', 'lms_player')

del (safeget)
