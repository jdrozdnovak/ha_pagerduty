"""The PagerDuty integration for Home Assistant."""

import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN, UPDATE_INTERVAL
from pdpyras import APISession

_LOGGER = logging.getLogger(__name__)


class PagerDutyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PagerDuty data."""

    def __init__(self, hass, session):
        """Initialize."""
        self.session = session
        super().__init__(
            hass, _LOGGER, name="PagerDuty", update_interval=UPDATE_INTERVAL
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            user = await self.hass.async_add_executor_job(self.fetch_user)
            user_id = user.get("id")
            on_calls = await self.hass.async_add_executor_job(
                self.fetch_on_calls, user_id
            )

            self.teams = {team["id"]: team["name"] for team in user.get("teams", [])}

            team_ids = list(self.teams.keys())
            services = await self.hass.async_add_executor_job(
                self.fetch_services, team_ids
            )
            service_ids = [service["id"] for service in services]
            incidents = await self.hass.async_add_executor_job(
                self.fetch_incidents, service_ids
            )

            return {"on_calls": on_calls, "services": services, "incidents": incidents}
        except Exception as e:
            _LOGGER.error(f"Error communicating with PagerDuty API: {e}")
            raise UpdateFailed(f"Error communicating with API: {e}")

    def fetch_user(self):
        """Fetch user data."""
        return self.session.rget("/users/me", params={"include[]": "teams"})

    def fetch_on_calls(self, user_id):
        """Fetch on-call data for the user."""
        if not user_id:
            return []
        params = {"user_ids[]": user_id}
        return self.session.rget("/oncalls", params=params)

    def fetch_services(self, team_ids):
        """Fetch services for given team IDs."""
        all_services = []
        for team_id in team_ids:
            services = self.session.list_all("services", params={"team_ids[]": team_id})
            for service in services:
                service["team_name"] = self.teams.get(team_id, "Unknown")
            all_services.extend(services)
        return all_services

    def fetch_incidents(self, service_ids):
        """Fetch incidents for given service IDs."""
        all_incidents = []
        for service_id in service_ids:
            incidents = self.session.list_all(
                "incidents",
                params={
                    "service_ids[]": service_id,
                    "statuses[]": ["acknowledged", "triggered"],
                },
            )
            all_incidents.extend(incidents)
        return all_incidents


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PagerDuty integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry):
    """Set up PagerDuty from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    update_interval = entry.options.get("update_interval", UPDATE_INTERVAL)

    session = APISession(api_key)
    coordinator = PagerDutyDataUpdateCoordinator(
        hass, session, update_interval=update_interval
    )
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("binary_sensor", DOMAIN, {}, entry)
    )
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, entry)
    )

    return True
