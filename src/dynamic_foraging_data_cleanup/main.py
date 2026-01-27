import json
import os

from upath import UPath
from pid.decorator import pidfile
from cyclopts import App
from loguru import logger

from dynamic_foraging_data_cleanup import __version__, APP_NAME, DATA_DIR, PYTHON_VERSION, PYTHON_EXE, PACKAGES
from dynamic_foraging_data_cleanup.config import Config, config_schema
from dynamic_foraging_data_cleanup.setup_loguru import setup_logger
from dynamic_foraging_data_cleanup.data_cleanup import data_cleanup

app = App()

app.command(config_schema)


@app.default
@logger.catch()
@pidfile()
def main() -> None:
    """Fetch config, setup logging, process a single dataset"""
    logger.info("Fetching config from server")
    config_server_url = UPath(
        os.getenv("ALLENINST_CONFIG_API_URL", "http://eng-tools:8888/api/v1beta/configs/projects/")
    )
    config_server_url = config_server_url / f"{APP_NAME}?rig_name={os.getenv('aibs_comp_id', 'unknown')}"
    try:
        config_data = json.loads(config_server_url.read_text())
    except Exception as e:
        logger.error(f"Failed to fetch config data: {e}")
        config_data = {}

    # instantiate config object
    config = Config(**config_data)  # will also pull from cli args

    # Set up loguru
    setup_logger(
        APP_NAME,
        __version__,
        log_file=DATA_DIR / "logs" / f"{APP_NAME}.log",
        logserver_url=config.logserver_url,
        extras={
            "rig_id": os.getenv("aibs_rig_id", "unknown"),
            "comp_id": os.getenv("aibs_comp_id", "unknown"),
            "software": APP_NAME,
            "version": __version__,
        },
    )

    logger.debug(
        f"Starting {APP_NAME}",
        python_version=PYTHON_VERSION,
        python_executable=PYTHON_EXE,
        package_versions=PACKAGES,
        **config.model_dump(),
    )

    ###### Perform your tool's business logic here ######
    data_cleanup(config)


if __name__ == "__main__":
    app()
