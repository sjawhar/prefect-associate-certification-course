from __future__ import annotations

import asyncio
import datetime
import random
from typing import TYPE_CHECKING

import httpx
import pandas as pd
import prefect
import prefect.artifacts
import prefect.input
import prefect.runtime.flow_run
import prefect.tasks

if TYPE_CHECKING:
    from prefect.client.schemas.objects import Flow, FlowRun, State


class Location(prefect.input.RunInput):
    lat: float
    lon: float


def on_completion(flow: Flow, flow_run: FlowRun, state: State):
    print(f"Flow {flow.name} run {flow_run.id} completed with state {state.type}.")


@prefect.task(
    cache_expiration=datetime.timedelta(hours=1),
    cache_key_fn=prefect.tasks.task_input_hash,
    retries=3,
    retry_delay_seconds=prefect.tasks.exponential_backoff(2),
)
def fetch_weather(lat: float, lon: float):
    if random.random() < 0.5:
        raise RuntimeError("Failed to fetch weather")

    base_url = "https://api.open-meteo.com/v1/forecast/"
    temps = httpx.get(
        base_url,
        params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m"},
    )
    temps.raise_for_status()
    forecasted_temp = float(temps.json()["hourly"]["temperature_2m"][0])
    return forecasted_temp


@prefect.task()
def save_weather(weather: float):
    with open("weather.csv", "w") as file:
        file.write(str(weather))
    return "Success!"


@prefect.task()
def report(lat: float, lon: float, weather: float):
    report = (
        pd.DataFrame.from_records(
            [
                {
                    "flow_run": prefect.runtime.flow_run.get_id(),
                    "lat": lat,
                    "lon": lon,
                    "temperature": weather,
                }
            ]
        )
        .set_index("flow_run")
        .to_markdown()
    )
    prefect.artifacts.create_markdown_artifact(
        key="weather-report",
        markdown=report,
        description="A report of the forecasted temperature.",
    )


@prefect.flow(name="fetch-weather", log_prints=True, on_completion=[on_completion])
async def pipeline(lat: float = 38.9, lon: float = -77.0):
    location = await prefect.pause_flow_run(
        wait_for_input=Location.with_initial_data(lat=lat, lon=lon),
    )
    weather = fetch_weather(lat=location.lat, lon=location.lon)
    result = save_weather(weather)
    report(lat=lat, lon=lon, weather=weather)
    return result


if __name__ == "__main__":
    asyncio.run(pipeline())
