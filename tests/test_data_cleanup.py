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
            path.mkdir(parents=True, exist_ok=True)

        # test identification with no deletion
        data_cleanup(config=Config(data_directory=tempdir, age_limit_days=0, actually_delete=False))
        assert all([path.exists() for path in dummy_data])

        # test actual deletion
        data_cleanup(config=Config(data_directory=tempdir, age_limit_days=0, actually_delete=True))
        assert all([not path.exists() for path in dummy_data[:3]]) and dummy_data[3].exists()


def test_subfolder_deletion():
    """Test deletion of specific subfolders within a dataset"""
    dummy_data = [
        Path("rig") / "769362" / "behavior_769362_2025-05-20_13-56-53",
        Path("rig") / "769362" / "behavior_769362_2025-05-20_13-56-53" / "behavior-videos",
        Path("rig") / "769362" / "behavior_769362_2025-05-20_13-56-53" / "behavior",
    ]

    with tempfile.TemporaryDirectory() as tempdir:
        dummy_data = [Path(tempdir) / path for path in dummy_data]
        for path in dummy_data:
            path.mkdir(parents=True, exist_ok=True)

        # Test deletion of subfolders only
        data_cleanup(
            config=Config(
                data_directory=tempdir,
                age_limit_days=1,
                actually_delete=True,
                subfolder_age={"behavior-videos": 0},
            )
        )

        assert dummy_data[0].exists()
        assert not dummy_data[1].exists()  # should be deleted
        assert dummy_data[2].exists()  # should remain


def test_doctest():
    doctest.testmod(verbose=True)
