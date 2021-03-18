from ert_data import loader
from tests.data.mocked_block_observation import MockedBlockObservation
import pandas as pd
import pytest
import deprecation

from unittest.mock import Mock, MagicMock


def create_summary_get_observations():
    return pd.DataFrame(
        [[10.0, None, 10.0, 10.0], [1.0, None, 1.0, 1.0]], index=["OBS", "STD"]
    )


def mocked_obs_node_get_index_nr(nr):
    return {0: 0, 1: 2, 2: 3}[nr]


@pytest.mark.parametrize(
    "obs_type",
    ["GEN_OBS", "SUMMARY_OBS", "BLOCK_OBS"],
)
def test_data_loader_factory(obs_type):
    assert loader.data_loader_factory(obs_type).func == loader._extract_data


def test_data_loader_factory_fails():
    with pytest.raises(TypeError):
        loader.data_loader_factory("BAD_TYPE")


def test_load_general_response(facade, monkeypatch):
    facade.load_gen_data.return_value = pd.DataFrame(data=[10.0, 10.0, 10.0, 10.0])
    facade.all_data_type_keys.return_value = ["some_key@1"]
    facade.is_gen_data_key.return_value = True

    result = loader._load_general_response(facade, "some_key", "test_case")

    facade.load_gen_data.assert_called_once_with("test_case", "some_key", 1)

    assert result.equals(
        pd.DataFrame(
            [[10.0, 10.0, 10.0, 10.0]],
            index=[0],
        )
    )


def test_load_general_obs(facade, monkeypatch):
    mock_node = MagicMock()
    mock_node.__len__.return_value = 3
    mock_node.get_data_points.return_value = [10.0, 20.0, 30.0]
    mock_node.get_std.return_value = [1.0, 2.0, 3.0]
    mock_node.getIndex.side_effect = mocked_obs_node_get_index_nr

    obs_mock = Mock()
    obs_mock.getDataKey.return_value = "test_data_key"
    obs_mock.getStepList.return_value.asList.return_value = [1]
    facade.get_observations.return_value = {"some_key": obs_mock}

    facade.load_gen_data.return_value = pd.DataFrame(data=[9.9, 19.9, 29.9, 39.9])
    facade.get_observations()["some_key"].getNode.return_value = mock_node

    result = loader._load_general_obs(facade, ["some_key"], "a_random_name")

    mock_node.get_data_points.assert_called_once_with()
    mock_node.get_std.assert_called_once_with()

    assert result.columns.to_list() == [
        ("some_key", 0, 0),
        ("some_key", 2, 2),
        ("some_key", 3, 3),
    ]
    assert result.index.to_list() == ["OBS", "STD"]
    assert all(result.values.flatten() == [10.0, 20.0, 30.0, 1.0, 2.0, 3.0])


@pytest.mark.parametrize(
    "func", [loader.data_loader_factory("GEN_OBS"), loader.load_general_data]
)
def test_load_general_data(facade, monkeypatch, func):
    def side_effect(val):
        if val == "some_key@2":
            return True
        return False

    mock_node = MagicMock()
    mock_node.__len__.return_value = 3
    mock_node.get_data_points.return_value = [10.0, 20.0, 30.0]
    mock_node.get_std.return_value = [1.0, 2.0, 3.0]
    mock_node.getIndex.side_effect = mocked_obs_node_get_index_nr

    obs_mock = Mock()
    obs_mock.getDataKey.return_value = "test_data_key"
    obs_mock.getStepList.return_value.asList.return_value = [1]
    facade.get_observations.return_value = {"some_key": obs_mock}

    facade.all_data_type_keys.return_value = ["some_key@2", "not_related_key@3"]
    facade.is_gen_data_key.side_effect = side_effect

    facade.load_gen_data.return_value = pd.DataFrame(data=[9.9, 19.9, 29.9, 39.9])
    facade.get_observations()["some_key"].getNode.return_value = mock_node

    facade.get_impl_type_name_for_obs_key.return_value = "GEN_OBS"

    result = func(facade, "some_key", "a_random_name")

    mock_node.get_data_points.assert_called_once_with()
    mock_node.get_std.assert_called_once_with()

    assert result.columns.to_list() == [
        ("some_key", 0, 0),
        ("some_key", 2, 2),
        ("some_key", 3, 3),
    ]
    assert result.index.to_list() == ["OBS", "STD", 0]
    assert all(
        result.values.flatten() == [10.0, 20.0, 30.0, 1.0, 2.0, 3.0, 9.9, 29.9, 39.9]
    )


@pytest.mark.usefixtures("facade")
def test_load_block_response(facade, monkeypatch):
    obs_mock = Mock()
    obs_mock.getStepList.return_value.asList.return_value = [1]
    facade.get_observations.return_value = {"some_key": obs_mock}

    mocked_get_block_measured = Mock(
        return_value=pd.DataFrame(data=[[10.0, 10.0, 10.0, 10.0]])
    )

    monkeypatch.setattr(loader, "_get_block_measured", mocked_get_block_measured)
    block_data = Mock()
    plot_block_data_loader = Mock()
    facade.create_plot_block_data_loader.return_value = plot_block_data_loader
    plot_block_data_loader.load.return_value = block_data

    mocked_block_obs = MockedBlockObservation(
        {"values": [10.0, None, 10.0, 10.0], "stds": [1.0, None, 1.0, 1.0]}
    )
    plot_block_data_loader.getBlockObservation.return_value = mocked_block_obs

    result = loader._load_block_response(facade, "some_key", "a_random_name")
    mocked_get_block_measured.assert_called_once_with(
        facade.get_ensemble_size(), block_data
    )
    assert result.equals(
        pd.DataFrame(
            [[10.0, 10.0, 10.0, 10.0]],
            index=[0],
        )
    )


@pytest.mark.parametrize(
    "func", [loader.data_loader_factory("SUMMARY_OBS"), loader.load_summary_data]
)
def test_load_summary_data(facade, monkeypatch, func):
    obs_mock = Mock()
    obs_mock.getStepList.return_value = [1, 2]

    facade.get_observations.return_value = {"some_key": obs_mock}
    facade.load_observation_data.return_value = pd.DataFrame(
        {
            "some_key": {"2010-01-10": 10, "2010-01-20": 20},
            "STD_some_key": {"2010-01-10": 0.1, "2010-01-20": 0.2},
        }
    )
    facade.load_all_summary_data.return_value = pd.DataFrame(
        {"some_key": [9.9, 19.9, 29.9]},
        index=pd.MultiIndex.from_tuples(
            [(0, "2010-01-10"), (0, "2010-01-20"), (0, "2021-02-10")],
            names=["Realization", "Date"],
        ),
    )
    facade.get_impl_type_name_for_obs_key.return_value = "SUMMARY_OBS"

    result = func(facade, "some_key", "a_random_name")

    assert result.columns.to_list() == [
        ("some_key", "2010-01-10", 0),
        ("some_key", "2010-01-20", 1),
    ]
    assert result.index.to_list() == ["OBS", "STD", 0]
    assert all(result.values.flatten() == [10.0, 20.0, 0.1, 0.2, 9.9, 19.9])


def test_load_summary_obs(facade, monkeypatch):
    obs_mock = Mock()
    obs_mock.getStepList.return_value = [1, 2]

    facade.get_observations.return_value = {"some_key": obs_mock}
    facade.load_observation_data.return_value = pd.DataFrame(
        {
            "some_key": {"2010-01-10": 10, "2010-01-20": 20},
            "STD_some_key": {"2010-01-10": 0.1, "2010-01-20": 0.2},
        }
    )

    result = loader._load_summary_obs(facade, ["some_key"], "a_random_name")

    assert result.columns.to_list() == [
        ("some_key", "2010-01-10", 0),
        ("some_key", "2010-01-20", 1),
    ]
    assert result.index.to_list() == ["OBS", "STD"]
    assert all(result.values.flatten() == [10.0, 20.0, 0.1, 0.2])


def test_load_summary_response(facade, monkeypatch):
    facade.load_all_summary_data.return_value = pd.DataFrame(
        {"some_key": [9.9, 19.9, 29.9]},
        index=pd.MultiIndex.from_tuples(
            [(0, "2010-01-10"), (0, "2010-01-20"), (0, "2021-02-10")],
            names=["Realization", "Date"],
        ),
    )

    result = loader._load_summary_response(facade, "some_key", "a_random_name")

    assert result.columns.to_list() == ["2010-01-10", "2010-01-20", "2021-02-10"]
    assert result.index.to_list() == [0]
    assert all(result.values.flatten() == [9.9, 19.9, 29.9])


def test_no_obs_error(facade, monkeypatch):
    obs_mock = pd.DataFrame()
    obs_loader = Mock(return_value=obs_mock)
    response_loader = Mock(return_value=pd.DataFrame([1, 2]))
    monkeypatch.setattr(loader, "_create_multi_index", MagicMock(return_value=[1]))
    facade.get_impl_type_name_for_obs_key.return_value = "SUMMARY_OBS"
    with pytest.raises(loader.ObservationError):
        loader._extract_data(
            facade,
            "some_key",
            "a_random_name",
            response_loader,
            obs_loader,
            "SUMMARY_OBS",
        )


def test_multiple_obs_types(facade, monkeypatch):
    facade.get_impl_type_name_for_obs_key.side_effect = [
        "SUMMARY_OBS",
        "SUMMARY_OBS",
        "BLOCK_OBS",
    ]
    with pytest.raises(
        loader.ObservationError,
        match=r"Found: \['SUMMARY_OBS', 'SUMMARY_OBS', 'BLOCK_OBS'\]",
    ):
        loader._extract_data(
            facade,
            ["some_summary_key", "another_summary_key", "block_key"],
            "a_random_name",
            Mock(),
            Mock(),
            "SUMMARY_OBS",
        )


def test_different_data_key(facade):
    facade.get_impl_type_name_for_obs_key.return_value = "SUMMARY_OBS"
    facade.get_data_key_for_obs_key.side_effect = [
        "data_key",
        "another_data_key",
        "data_key",
    ]
    with pytest.raises(
        loader.ObservationError,
        match=r"found: \['data_key', 'another_data_key', 'data_key'\]",
    ):
        loader._extract_data(
            facade,
            ["obs_1", "obs_2", "obs_3"],
            "a_random_name",
            Mock(),
            Mock(),
            "SUMMARY_OBS",
        )


@deprecation.fail_if_not_removed
@pytest.mark.parametrize(
    "func", [loader.load_general_data, loader.load_summary_data, loader.load_block_data]
)
def test_deprecated_entry_points(facade, monkeypatch, func):
    facade = MagicMock()
    extract_data = MagicMock()
    monkeypatch.setattr(loader, "_extract_data", extract_data)
    func(facade, ["obs_1", "obs_2"], "case_name", include_data=False)
