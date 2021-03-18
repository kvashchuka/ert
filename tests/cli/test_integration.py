from ert_shared.feature_toggling import FeatureToggling
import pytest
import os
import shutil
import threading
import ert_shared
from ert_shared.main import ert_parser
from argparse import ArgumentParser
from ert_shared.cli.main import run_cli
from ert_shared.cli import ENSEMBLE_SMOOTHER_MODE, TEST_RUN_MODE

from unittest.mock import Mock


@pytest.fixture()
def mock_cli_run(monkeypatch):
    mocked_monitor = Mock()
    mocked_thread_start = Mock()
    mocked_thread_join = Mock()
    monkeypatch.setattr(threading.Thread, "start", mocked_thread_start)
    monkeypatch.setattr(threading.Thread, "join", mocked_thread_join)
    monkeypatch.setattr(ert_shared.cli.monitor.Monitor, "monitor", mocked_monitor)
    yield mocked_monitor, mocked_thread_join, mocked_thread_start


def test_target_case_equal_current_case(tmpdir, source_root):
    shutil.copytree(
        os.path.join(source_root, "test-data", "local", "poly_example"),
        os.path.join(str(tmpdir), "poly_example"),
    )
    with tmpdir.as_cwd():
        parser = ArgumentParser(prog="test_main")
        parsed = ert_parser(
            parser,
            [
                ENSEMBLE_SMOOTHER_MODE,
                "--current-case",
                "test_case",
                "--target-case",
                "test_case",
                "poly_example/poly.ert",
            ],
        )

        with pytest.raises(SystemExit):
            run_cli(parsed)


def test_runpath_file(tmpdir, source_root):
    shutil.copytree(
        os.path.join(source_root, "test-data", "local", "poly_example"),
        os.path.join(str(tmpdir), "poly_example"),
    )

    config_lines = [
        "LOAD_WORKFLOW_JOB ASSERT_RUNPATH_FILE\n" "LOAD_WORKFLOW TEST_RUNPATH_FILE\n",
        "HOOK_WORKFLOW TEST_RUNPATH_FILE PRE_SIMULATION\n",
    ]

    with tmpdir.as_cwd():
        with open("poly_example/poly.ert", "a") as fh:
            fh.writelines(config_lines)

        parser = ArgumentParser(prog="test_main")
        parsed = ert_parser(
            parser,
            [
                ENSEMBLE_SMOOTHER_MODE,
                "--target-case",
                "poly_runpath_file",
                "--realizations",
                "1,2,4,8,16,32,64",
                "poly_example/poly.ert",
            ],
        )

        run_cli(parsed)

        assert os.path.isfile("RUNPATH_WORKFLOW_0.OK")
        assert os.path.isfile("RUNPATH_WORKFLOW_1.OK")


def test_ensemble_evaluator(tmpdir, source_root):
    shutil.copytree(
        os.path.join(source_root, "test-data", "local", "poly_example"),
        os.path.join(str(tmpdir), "poly_example"),
    )

    with tmpdir.as_cwd():
        parser = ArgumentParser(prog="test_main")
        parsed = ert_parser(
            parser,
            [
                ENSEMBLE_SMOOTHER_MODE,
                "--target-case",
                "poly_runpath_file",
                "--realizations",
                "1,2,4,8,16,32,64",
                "--enable-ensemble-evaluator",
                "poly_example/poly.ert",
            ],
        )
        FeatureToggling.update_from_args(parsed)

        assert FeatureToggling.is_enabled("ensemble-evaluator") is True

        run_cli(parsed)
        FeatureToggling.reset()


def test_ensemble_evaluator_disable_monitoring(tmpdir, source_root):
    shutil.copytree(
        os.path.join(source_root, "test-data", "local", "poly_example"),
        os.path.join(str(tmpdir), "poly_example"),
    )

    with tmpdir.as_cwd():
        parser = ArgumentParser(prog="test_main")
        parsed = ert_parser(
            parser,
            [
                ENSEMBLE_SMOOTHER_MODE,
                "--enable-ensemble-evaluator",
                "--disable-monitoring",
                "--target-case",
                "poly_runpath_file",
                "--realizations",
                "1,2,4,8,16,32,64",
                "poly_example/poly.ert",
            ],
        )
        FeatureToggling.update_from_args(parsed)

        assert FeatureToggling.is_enabled("ensemble-evaluator") is True

        run_cli(parsed)
        FeatureToggling.reset()


def test_cli_test_run(tmpdir, source_root, mock_cli_run):
    shutil.copytree(
        os.path.join(source_root, "test-data", "local", "poly_example"),
        os.path.join(str(tmpdir), "poly_example"),
    )

    with tmpdir.as_cwd():
        parser = ArgumentParser(prog="test_main")
        parsed = ert_parser(parser, [TEST_RUN_MODE, "poly_example/poly.ert"])
        run_cli(parsed)

    monitor_mock, thread_join_mock, thread_start_mock = mock_cli_run
    monitor_mock.assert_called_once()
    thread_join_mock.assert_called_once()
    thread_start_mock.assert_called_once()
