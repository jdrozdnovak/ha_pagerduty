import logging
import datetime
from pdpyras import APISession, PDClientError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# Wrapper functions for fetching data from PagerDuty
def fetch_user_teams_wrapper(session):
    return session.rget("users/me", params={"include[]": "teams"})


def fetch_on_call_data_wrapper(session, user_id):
    return session.list_all("oncalls", params={"user_ids[]": user_id})


def fetch_services_wrapper(session, team_id):
    return session.list_all("services", params={"team_ids[]": team_id})


def fetch_incidents_wrapper(session, service_id):
    return session.list_all(
        "incidents",
        params={
            "service_ids[]": service_id,
            "statuses[]": ["triggered", "acknowledged"],
        },
    )


class PagerDutyDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the PagerDuty API."""

    def __init__(self, hass, api_token, update_interval):
        _LOGGER.debug("Initializing PagerDuty Data Coordinator")
        self.session = APISession(api_token)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def fetch_user_teams(self):
        _LOGGER.debug("Fetching user teams from PagerDuty")
        try:
            user_info = await self.hass.async_add_executor_job(
                fetch_user_teams_wrapper, self.session
            )
            _LOGGER.debug("Received user info: %s", user_info)
            if "teams" in user_info:
                user_id = user_info["id"]
                teams = [
                    {"id": team["id"], "name": team["name"]}
                    for team in user_info["teams"]
                ]
                return user_id, teams
            else:
                raise UpdateFailed("Unexpected structure in user info response")
        except PDClientError as e:
            _LOGGER.error("Error fetching user teams from PagerDuty: %s", e)
            raise UpdateFailed(f"Error fetching user teams from PagerDuty: {e}")

    async def fetch_on_call_data(self, user_id):
        _LOGGER.debug("Fetching on-call data for user ID: %s", user_id)
        try:
            on_calls = await self.hass.async_add_executor_job(
                fetch_on_call_data_wrapper, self.session, user_id
            )
            _LOGGER.debug("Received on-call data: %s", on_calls)
            return len(on_calls) > 0
        except PDClientError as e:
            _LOGGER.error("Error fetching on-call data from PagerDuty: %s", e)
            raise UpdateFailed(f"Error fetching on-call data from PagerDuty: {e}")

    async def _async_update_data(self):
        _LOGGER.debug("Updating PagerDuty data")
        try:
            user_id, user_teams = await self.fetch_user_teams()
            on_call_active = await self.fetch_on_call_data(user_id)
            _LOGGER.debug("On-call active: %s", on_call_active)

            parsed_data = {}
            for team_id, team_name in user_teams:
                _LOGGER.debug("Fetching services for team ID: %s", team_id)
                services = await self.hass.async_add_executor_job(
                    fetch_services_wrapper, self.session, team_id
                )

                for service in services:
                    service_id = service["id"]
                    service_name = service["name"]
                    _LOGGER.debug("Fetching incidents for service ID: %s", service_id)
                    incidents = await self.hass.async_add_executor_job(
                        fetch_incidents_wrapper, self.session, service_id
                    )

                    incident_count = sum(1 for incident in incidents)
                    high_urgency_count = sum(
                        1 for incident in incidents if incident["urgency"] == "high"
                    )
                    low_urgency_count = sum(
                        1 for incident in incidents if incident["urgency"] == "low"
                    )

                    triggered_count = sum(
                        1 for incident in incidents if incident["status"] == "triggered"
                    )
                    acknowledged_count = sum(
                        1
                        for incident in incidents
                        if incident["status"] == "acknowledged"
                    )

                    parsed_data[service_id] = {
                        "team_id": team_id,
                        "team_name": team_name,
                        "service_name": service_name,
                        "triggered_count": triggered_count,
                        "acknowledged_count": acknowledged_count,
                        "high_urgency_count": high_urgency_count,
                        "low_urgency_count": low_urgency_count,
                        "incident_count": incident_count,
                        "on_call_data": on_call_active,
                    }
            _LOGGER.debug("Completed updating PagerDuty data")
            return parsed_data
        except Exception as e:
            _LOGGER.error("Exception occurred while updating data: %s", e)
            raise UpdateFailed(f"Exception during data update: {e}")
