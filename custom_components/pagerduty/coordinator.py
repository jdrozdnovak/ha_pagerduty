from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import logging

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

    async def async_update_data(self):
        """Fetch data from API."""
        try:
            _LOGGER.debug("Fetching user information from PagerDuty")
            user = await self.hass.async_add_executor_job(
                self.session.rget, "/users/me", params={"include[]": "teams"}
            )

            # Extract and store team information
            self.teams = {team["id"]: team["name"] for team in user.get("teams", [])}
            _LOGGER.debug(f"Teams: {self.teams}")

            # Fetch on-call data
            _LOGGER.debug("Fetching on-call data")
            on_calls = await self.hass.async_add_executor_job(
                self.session.rget, "oncalls", params={"user_ids[]": user.get("id")}
            )

            # Fetch incidents for each team
            incidents = {}
            for team_id in self.teams.keys():
                _LOGGER.debug(f"Fetching incidents for team {team_id}")
                team_incidents = await self.hass.async_add_executor_job(
                    self.session.list_all,
                    "incidents",
                    params={
                        "team_ids[]": team_id,
                        "statuses[]": ["acknowledged", "triggered"],
                    },
                )
                incidents[team_id] = team_incidents

            _LOGGER.debug(f"Received incidents: {incidents}")
            return {"teams": self.teams, "on_calls": on_calls, "incidents": incidents}
        except Exception as e:
            _LOGGER.error(f"Error communicating with PagerDuty API: {e}")
            raise UpdateFailed(f"Error communicating with API: {e}")
