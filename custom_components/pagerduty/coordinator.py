from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

class PagerDutyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PagerDuty data."""

    def __init__(self, hass, session):
        """Initialize."""
        self.session = session

        update_interval = timedelta(minutes=1)
        super().__init__(hass, _LOGGER, name="PagerDuty", update_interval=update_interval)

    async def async_update_data(self):
        """Fetch data from API."""
        try:
            _LOGGER.debug("Fetching user information from PagerDuty")
            user = await self.hass.async_add_executor_job(self.session.rget, "/users/me")
            user_id = user.get("id", None)
            if user_id is None:
                _LOGGER.warning("No user ID found in PagerDuty response")
                return []

            _LOGGER.debug(f"Fetching on-call data for user {user_id} from PagerDuty")
            on_calls = await self.hass.async_add_executor_job(self.session.rget, "oncalls", {"user_ids[]": user_id})
            
            _LOGGER.debug(f"Received on-call data: {on_calls}")
            return on_calls
        except Exception as e:
            _LOGGER.error(f"Error communicating with PagerDuty API: {e}")
            raise UpdateFailed(f"Error communicating with API: {e}")
