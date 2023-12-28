import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)


class PagerDutyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PagerDuty data."""

    def __init__(self, hass, session, update_interval, ignored_team_ids):
        """Initialize."""
        self.session = session
        self.ignored_team_ids = ignored_team_ids
        super().__init__(
            hass, _LOGGER, name="PagerDuty", update_interval=update_interval
        )

    async def async_first_config_entry(self):
        """Custom method to handle the first update of the config entry."""
        try:
            await self.async_refresh()
        except UpdateFailed:
            _LOGGER.warning(
                "Initial data update failed, will retry in background"
            )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            user = await self.hass.async_add_executor_job(self.fetch_user)
            user_id = user.get("id")
            on_calls = await self.hass.async_add_executor_job(
                self.fetch_on_calls, user_id
            )

            self.teams = {
                team["id"]: team["name"] for team in user.get("teams", [])
            }

            team_ids = list(self.teams.keys())
            services = await self.hass.async_add_executor_job(
                self.fetch_services, team_ids
            )
            if self.ignored_team_ids:
                services = [
                    s
                    for s in services
                    if s["team_id"] not in self.ignored_team_ids
                ]
            service_ids = [service["id"] for service in services]
            incidents = await self.hass.async_add_executor_job(
                self.fetch_incidents, service_ids
            )

            return {
                "on_calls": on_calls,
                "services": services,
                "incidents": incidents,
                "user_id": user_id,
            }
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
            services = self.session.list_all(
                "services", params={"team_ids[]": team_id}
            )
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
                    "include[]": "users",
                },
            )
            all_incidents.extend(incidents)
        return all_incidents
