from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN
import logging

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    _LOGGER.debug("Setting up PagerDuty integration")
    hass.data[DOMAIN] = {}
    _LOGGER.debug("PagerDuty integration setup complete")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug(f"Setting up PagerDuty entry: {entry.entry_id}")
    sensor_setup = hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    binary_sensor_setup = hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )
    _LOGGER.debug("Awaiting sensor and binary sensor setup")
    await sensor_setup
    await binary_sensor_setup
    _LOGGER.debug(f"PagerDuty entry setup complete: {entry.entry_id}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug(f"Unloading PagerDuty entry: {entry.entry_id}")
    unload_sensor_ok = await hass.config_entries.async_forward_entry_unload(
        entry, "sensor"
    )
    _LOGGER.debug(
        f"Sensor platform unload {'successful' if unload_sensor_ok else 'failed'} for {entry.entry_id}"
    )
    unload_binary_sensor_ok = await hass.config_entries.async_forward_entry_unload(
        entry, "binary_sensor"
    )
    _LOGGER.debug(
        f"Binary sensor platform unload {'successful' if unload_binary_sensor_ok else 'failed'} for {entry.entry_id}"
    )
    if unload_sensor_ok and unload_binary_sensor_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug(f"PagerDuty entry unloaded: {entry.entry_id}")
    return unload_sensor_ok and unload_binary_sensor_ok
