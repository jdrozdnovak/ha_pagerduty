"""The PagerDuty integration for Home Assistant."""

import logging
from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_API_KEY, Platform, CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from datetime import timedelta
from .const import DOMAIN
from pdpyras import APISession
from .coordinator import PagerDutyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PagerDuty integration."""
    _LOGGER.debug("Setting up PagerDuty integration")
    _LOGGER.debug(f"Configuration data: {config}")

    if DOMAIN not in config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )

    return True


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up PagerDuty from a config entry."""

    _LOGGER.debug(f"Setting up config entry: {entry}")

    api_key = entry.data[CONF_API_KEY]
    ignored_team_ids = entry.data.get("ignored_team_ids", "")
    api_base_url = entry.data.get("api_base_url")
    session = APISession(api_key)
    session.url = api_base_url

    _LOGGER.debug(f"Ignored team IDs: {ignored_team_ids}")
    _LOGGER.debug(f"API base URL: {api_base_url}")

    coordinator = PagerDutyDataUpdateCoordinator(
        hass, session, ignored_team_ids
    )

    await coordinator.async_first_config_entry()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    user_id = entry.data.get("user_id", "default_user_id")
    unique_device_name = f"PagerDuty_{user_id}"

    device_registry = async_get_device_registry(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, unique_device_name)},
        name=unique_device_name,
        manufacturer="PagerDuty Inc.",
    )

    hass.data[DOMAIN][entry.entry_id]["device_id"] = device.id

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {
                CONF_NAME: DOMAIN,
                CONF_API_KEY: api_key,
                "api_base_url": api_base_url,
            },
            entry.data,
        )
    )

    return True
