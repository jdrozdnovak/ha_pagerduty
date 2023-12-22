from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import logging
from collections import defaultdict

_LOGGER = logging.getLogger(__name__)


class PagerDutyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PagerDuty data."""

    def __init__(self, hass, session):
        """Initialize."""
        self.session = session
        self.teams = {}  # Stores team IDs and names
        update_interval = timedelta(minutes=1)
        super().__init__(
            hass, _LOGGER, name="PagerDuty", update_interval=update_interval
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            user = await self.hass.async_add_executor_job(self.fetch_user)
            self.teams = {team["id"]: team["name"] for team in user.get("teams", [])}

            on_calls = await self.hass.async_add_executor_job(
                self.fetch_on_calls, user.get("id")
            )

            incidents = {}
            services = {}
            for team_id in self.teams.keys():
                team_services = await self.hass.async_add_executor_job(
                    self.fetch_services, team_id
                )
                services[team_id] = {
                    service["id"]: service for service in team_services
                }

                team_incidents = await self.hass.async_add_executor_job(
                    self.fetch_incidents, team_id
                )
                incidents[team_id] = defaultdict(
                    list, {inc["service"]["id"]: inc for inc in team_incidents}
                )

            return {
                "teams": self.teams,
                "on_calls": on_calls,
                "incidents": incidents,
                "services": services,
            }
        except Exception as e:
            _LOGGER.error(f"Error communicating with PagerDuty API: {e}")
            raise UpdateFailed(f"Error communicating with API: {e}")

    def fetch_user(self):
        """Fetch user data."""
        return self.session.rget("/users/me", params={"include[]": "teams"})

    def fetch_on_calls(self, user_id):
        """Fetch on-call data."""
        return self.session.rget("oncalls", params={"user_ids[]": user_id})

    def fetch_incidents(self, team_id):
        """Fetch incidents for a team."""
        return self.session.list_all(
            "incidents",
            params={"team_ids[]": team_id, "statuses[]": ["acknowledged", "triggered"]},
        )

    def fetch_services(self, team_id):
        """Fetch services for a team."""
        return self.session.list_all("services", params={"team_ids[]": team_id})
