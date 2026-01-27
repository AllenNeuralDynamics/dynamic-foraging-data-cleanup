"""
Run this script with
    `uv run data_cleanup.py`

By default, it won't actually delete anything, but it will print "Identified deletable dataset {}".
To actually delete the deletable things, add `--actually_delete True`

Calling `uv run data_cleanup.py --test` will run doctests and a test_data_cleanup function.
"""

import time
import os
from pathlib import Path
import shutil

from aind_data_access_api.document_db import MetadataDbClient
from pydantic import BaseModel

from loguru import logger

from dynamic_foraging_data_cleanup.config import Config


def data_cleanup(config: Config):
    data = find_deletable_data_dynamic_frg(
        config.data_directory,
        config.age_limit_days,
        config.too_old_for_warning_days,
    )
    deletable_datasets = [d for d in data if d.ok_to_delete]

    logger.info(f"Found {len(data)} total datasets, {len(deletable_datasets)} deletable")

    total_deleted_mb = 0
    for dataset in deletable_datasets:
        with logger.contextualize(**dataset.model_dump()):
            if config.actually_delete:
                logger.info(f"Deleting dataset {dataset.session_name}")
                with logger.catch(message="Could not remove folder"):
                    shutil.rmtree(dataset.folder)
                    total_deleted_mb += dataset.size_mb
            else:
                logger.info(f"Identified deletable dataset {dataset.session_name}")

    logger.info(
        f"Deleted {total_deleted_mb} mB of data across {len(deletable_datasets)} datasets",
        **config.model_dump(),
    )


#############################  Utilities


@logger.catch(message="Docdb query failed")
def query_docdb(filters: dict[str, str]) -> list[dict]:
    """Query AIND document database

    Potential filters:
        subject.subject_id
        name

    Examples:
        >>> response = query_docdb({'subject.subject_id': '791093'})
        >>> print(len(response) > 0)
        True
    """

    API_GATEWAY_HOST = "api.allenneuraldynamics.org"
    DATABASE = "metadata_index"
    COLLECTION = "data_assets"

    docdb_api_client = MetadataDbClient(
        host=API_GATEWAY_HOST,
        database=DATABASE,
        collection=COLLECTION,
    )
    response = docdb_api_client.retrieve_docdb_records(
        filter_query=filters,
    )
    logger.trace("Recieved {n} records from docdb", filters=filters)
    return response


def asset_exists_in_docdb(asset_name: str) -> bool:
    """Checks if an asset exists in the docdb

    Examples:
        >>> asset_exists_in_docdb("behavior_791093_2025-05-09_11-40-58")
        True
        >>> asset_exists_in_docdb("nope")
        False
    """
    return len(query_docdb({"name": asset_name})) == 1


def days_since_last_modification(path: str | Path) -> float:
    """Calculate age of file since last modification

    Examples:
        >>> age = days_since_last_modification(Path.home()) # returns something like 5.0726646920652305

        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile() as fp:
        ...     time1 = days_since_last_modification(fp.name)
        ...     time.sleep(0.1)
        ...     time2 = days_since_last_modification(fp.name)
        ...     print(time2 > time1)
        True
    """
    now = time.time()
    mod_time = os.path.getmtime(path)
    age_days = (now - mod_time) / 3600 / 24
    return age_days


def calculate_folder_size_mb(folder: Path) -> float:
    total_size = 0
    for path in folder.rglob("*"):
        if path.is_file():
            total_size += path.stat().st_size
    return total_size / 1024 / 1024


#############################


class Dataset(BaseModel):
    mouse_id: str
    session_name: str
    rig: str
    folder: Path
    folder_age: float
    exists_in_docdb: bool
    ok_to_delete: bool = False
    size_mb: float


def find_deletable_data_dynamic_frg(
    data_directory: Path,
    age_limit_days: int = 14,
    too_old_for_warning_days: int = 30,
) -> list[Dataset]:
    """Walk through data in a folder with this structure:

    447-1-B
        750034                                     <-------  mouse id
            behavior_750034_2025-03-28_11-06-44    <-------  session id
        769362
            behavior_769362_2025-05-19_13-21-31
            behavior_769362_2025-05-20_13-56-53
        ...

    """
    logger.info(f"Searching for data in {data_directory}")
    data = []
    for rig_folder in data_directory.glob("*"):
        for mouse_folder in rig_folder.glob("*"):
            if not mouse_folder.is_dir():
                continue
            for session_folder in mouse_folder.glob("*"):
                if not session_folder.is_dir():
                    continue
                dataset = Dataset(
                    mouse_id=mouse_folder.name,
                    session_name=session_folder.name,
                    rig=rig_folder.name,
                    folder=session_folder,
                    folder_age=days_since_last_modification(session_folder),
                    exists_in_docdb=asset_exists_in_docdb(session_folder.name),
                    size_mb=calculate_folder_size_mb(session_folder),
                )
                dataset.ok_to_delete = dataset.folder_age > age_limit_days and dataset.exists_in_docdb
                data.append(dataset)
                if age_limit_days < dataset.folder_age < too_old_for_warning_days and not dataset.exists_in_docdb:
                    logger.warning(f"Dataset '{dataset.session_name}' is old but not in docdb")
    return data
