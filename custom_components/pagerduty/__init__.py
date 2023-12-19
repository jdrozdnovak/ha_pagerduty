from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, CONF_NAME
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN

CONFIG_SCHEMA = cv.config_entry_only_config_schema()

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the PagerDuty component."""
    # This method is for setting up the component globally if needed
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PagerDuty from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Add setup for sensor platform here
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    # Unload the sensor platform
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    # Clean up any data if needed
    hass.data[DOMAIN].pop(entry.entry_id)

    return True
