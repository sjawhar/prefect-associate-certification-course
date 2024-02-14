import prefect

import pacc.fetch_weather


@prefect.flow()
def mega_flow():
    location = pacc.fetch_weather.Location(lat=38.9, lon=-77.0)
    result = pacc.fetch_weather.pipeline(lat=location.lat, lon=location.lon)
    print(type(result), result)
    return result


if __name__ == "__main__":
    mega_flow()
