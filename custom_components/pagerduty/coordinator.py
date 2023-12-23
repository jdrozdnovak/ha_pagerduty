from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)


class PagerDutyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PagerDuty data."""

    def __init__(self, hass, session):
        """Initialize."""
        self.session = session
        self.services = {}  # Stores service IDs and details
        update_interval = timedelta(minutes=1)
        super().__init__(
            hass, _LOGGER, name="PagerDuty", update_interval=update_interval
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            user = await self.hass.async_add_executor_job(self.fetch_user)
            team_ids = [team["id"] for team in user.get("teams", [])]

            # Fetch services for each team
            services = await self.hass.async_add_executor_job(
                self.fetch_services, team_ids
            )

            # Fetch incidents for each service
            service_ids = [service["id"] for service in services]
            incidents = await self.hass.async_add_executor_job(
                self.fetch_incidents, service_ids
            )

            return {"services": services, "incidents": incidents}
        except Exception as e:
            _LOGGER.error(f"Error communicating with PagerDuty API: {e}")
            raise UpdateFailed(f"Error communicating with API: {e}")

    def fetch_user(self):
        """Fetch user data."""
        return self.session.rget("/users/me", params={"include[]": "teams"})

    def fetch_services(self, team_ids):
        """Fetch services for given team IDs."""
        all_services = []
        for team_id in team_ids:
            services = self.session.list_all("services", params={"team_ids[]": team_id})
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
