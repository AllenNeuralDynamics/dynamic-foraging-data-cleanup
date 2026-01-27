import doctest
from pathlib import Path
import tempfile


from dynamic_foraging_data_cleanup.config import Config
from dynamic_foraging_data_cleanup.data_cleanup import data_cleanup


def test_data_cleanup():
    """Tests the main functionality with some dummy data"""

    dummy_data = [
        Path("rig") / "750034" / "behavior_750034_2025-03-28_11-06-44",  # first three are real assets in docdb
        Path("rig") / "769362" / "behavior_769362_2025-05-19_13-21-31",
        Path("rig") / "769362" / "behavior_769362_2025-05-20_13-56-53",
        Path("rig") / "769362" / "nope",
    ]
    with tempfile.TemporaryDirectory() as tempdir:
        dummy_data = [Path(tempdir) / path for path in dummy_data]
        for path in dummy_data:
            path.mkdir(parents=True)

        # test identification with no deletion
        data_cleanup(config=Config(data_directory=tempdir, age_limit_days=0, actually_delete=False))
        assert all([path.exists() for path in dummy_data])

        # test actual deletion
        data_cleanup(config=Config(data_directory=tempdir, age_limit_days=0, actually_delete=True))
        assert all([not path.exists() for path in dummy_data[:3]]) and dummy_data[3].exists()


def test_doctest():
    doctest.testmod(verbose=True)
