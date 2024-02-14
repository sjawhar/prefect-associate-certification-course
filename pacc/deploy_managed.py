import argparse

import prefect

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("DEPLOY_TYPE", choices=["source", "image"])
    args = parser.parse_args()

    flow: prefect.Flow = prefect.flow.from_source(
        source="https://github.com/sjawhar/prefect-associate-certification-course.git",
        entrypoint="pacc/fetch_weather.py:pipeline",
    )
    if args.DEPLOY_TYPE == "source":
        flow.deploy(
            name="fetch-weather-managed",
            work_pool_name="fetch-weather",
        )
    else:
        flow.deploy(
            name="fetch-weather-docker",
            push=False,
            image="sjawhar/fetch-weather:0.1",
            work_pool_name="fetch-weather-docker",
        )
