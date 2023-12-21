import logging
import datetime
from pdpyras import APISession, PDClientError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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
        """Initialize the data coordinator."""
        _LOGGER.debug("Initializing PagerDuty Data Coordinator")
        self.session = APISession(api_token)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def fetch_user_teams(self):
        """Fetch user teams from PagerDuty."""
        try:
            _LOGGER.debug("Fetching PagerDuty user teams")
            user_info = await self.hass.async_add_executor_job(
                fetch_user_teams_wrapper, self.session
            )
            _LOGGER.debug("User info: %s", user_info)

            if "user" in user_info and "teams" in user_info["user"]:
                user_id = user_info["user"]["id"]
                teams = [
                    {"id": team["id"], "name": team["name"]}
                    for team in user_info["user"]["teams"]
                ]
                return user_id, teams
            else:
                _LOGGER.error(
                    "Unexpected structure in user info response: %s", user_info
                )
                raise UpdateFailed("Unexpected structure in user info response")

        except PDClientError as e:
            _LOGGER.error("Error fetching user teams from PagerDuty: %s", e)
            raise UpdateFailed(f"Error fetching user teams from PagerDuty: {e}")

    async def fetch_on_call_data(self, user_id):
        """Fetch on-call data from PagerDuty."""
        try:
            _LOGGER.debug("Fetching PagerDuty on-call data")
            on_calls = await self.hass.async_add_executor_job(
                fetch_on_call_data_wrapper, self.session, user_id
            )
            on_call_data = []
            closest_on_call_start = None
            closest_on_call = None
            current_time = datetime.datetime.now()

            for on_call in on_calls:
                start = on_call.get("start")
                end = on_call.get("end")

                if start:
                    start = datetime.datetime.fromisoformat(start)
                if end:
                    end = datetime.datetime.fromisoformat(end)

                if start and start > current_time:
                    if closest_on_call_start is None or start < closest_on_call_start:
                        closest_on_call_start = start
                        closest_on_call = on_call

                schedule_id = None
                schedule_name = None
                if on_call.get("schedule"):
                    schedule_id = on_call["schedule"].get("id")
                    schedule_name = on_call["schedule"].get("summary")

                on_call_data.append(
                    {
                        "schedule_id": schedule_id,
                        "schedule_name": schedule_name,
                        "start": start,
                        "end": end,
                        "escalation_level": on_call.get("escalation_level"),
                    }
                )

            if closest_on_call:
                closest_schedule_id = (
                    closest_on_call["schedule"].get("id")
                    if closest_on_call.get("schedule")
                    else None
                )
                closest_schedule_name = (
                    closest_on_call["schedule"].get("summary")
                    if closest_on_call.get("schedule")
                    else None
                )
                closest_start = closest_on_call_start if closest_on_call_start else None
                closest_end = (
                    closest_on_call.get("end") if closest_on_call.get("end") else None
                )

                on_call_data.append(
                    {
                        "schedule_id": closest_schedule_id,
                        "schedule_name": closest_schedule_name,
                        "start": closest_start,
                        "end": closest_end,
                        "escalation_level": closest_on_call.get("escalation_level"),
                        "is_closest": True,
                    }
                )

            return on_call_data
        except PDClientError as e:
            _LOGGER.error("Error fetching on-call data from PagerDuty: %s", e)
            raise UpdateFailed(f"Error fetching on-call data from PagerDuty: {e}")

    async def _async_update_data(self):
        """Fetch data from the PagerDuty API."""
        user_id, user_teams = await self.fetch_user_teams()
        on_call_data = await self.fetch_on_call_data(user_id)

        parsed_data = {}
        for team_id, team_name in user_teams:
            _LOGGER.debug("Fetching PagerDuty services for team ID: %s", team_id)
            services = await self.hass.async_add_executor_job(
                fetch_services_wrapper, self.session, team_id
            )

            for service in services:
                service_id = service["id"]
                service_name = service["name"]
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
                    1 for incident in incidents if incident["status"] == "acknowledged"
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
                    "on_call_data": on_call_data,
                }

        return parsed_data
