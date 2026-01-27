from pathlib import Path
from typing import Optional
import json

from pydantic_settings import BaseSettings


class Config(
    BaseSettings,
    validate_default=True,
    extra="ignore",
):
    """Configuration object.
    Values below are defaults, which can be overridden by passing kwargs when instantiating:

    Config(**kwargs)

    or via environment variables. If env_prefix is set, environment variables should be prefixed accordingly.
    """

    data_directory: Path
    age_limit_days: int = 14
    actually_delete: bool = False
    logserver_url: str = "eng-logtools.corp.alleninstitute.org:9000"
    too_old_for_warning_days: int = 30
    # subfolder_age: dict = {
    #     "behavior": 14,
    #     "behavior-videos": 1,
    # }


def config_schema(file: Optional[Path] = None) -> dict:
    """Return the jsonschema for the Config class.

    Args:
        file: Optional Path to write the schema to as a JSON file.
    """
    schema = Config.model_json_schema()
    if file is not None:
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("w") as f:
            json.dump(schema, f, indent=2)
    return json.dumps(schema)
