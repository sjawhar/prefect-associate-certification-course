import datetime
import random

import httpx
import pandas as pd
import prefect
import prefect.artifacts
import prefect.tasks


@prefect.task(
    cache_expiration=datetime.timedelta(hours=1),
    cache_key_fn=prefect.tasks.task_input_hash,
    retries=3,
    retry_delay_seconds=prefect.tasks.exponential_backoff(2),
)
def fetch_weather(lat: float = 38.9, lon: float = -77.0):
    if random.random() < 0.5:
        raise RuntimeError("Failed to fetch weather")

    base_url = "https://api.open-meteo.com/v1/forecast/"
    temps = httpx.get(
        base_url,
        params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m"},
    )
    forecasted_temp = float(temps.json()["hourly"]["temperature_2m"][0])
    return forecasted_temp


@prefect.task()
def save_weather(weather: float):
    with open("weather.csv", "w") as file:
        file.write(str(weather))
    return "Success!"


@prefect.task()
def report(lat: float, lon: float, weather: float):
    report = pd.DataFrame.from_records(
        [{"lat": lat, "lon": lon, "temperature": weather}]
    ).to_markdown()
    raise ImportError()
    prefect.artifacts.create_markdown_artifact(
        key="weather-report",
        markdown=report,
        description="A report of the forecasted temperature.",
    )


@prefect.flow(name="fetch-weather")
def pipeline(lat: float = 38.9, lon: float = -77.0):
    weather = fetch_weather(lat=lat, lon=lon)
    result = save_weather(weather)
    report(lat=lat, lon=lon, weather=weather)
    return result


if __name__ == "__main__":
    pipeline.serve(name="fetch-weather", tags=["production"])
