import threading
import pytest
from functools import partial
from ert_shared.ensemble_evaluator.prefect_ensemble.client import Client
from tests.ensemble_evaluator.conftest import _mock_ws


def test_invalid_server():
    port = 7777
    host = "localhost"
    url = f"ws://{host}:{port}"

    with Client(url, max_retries=2, timeout_multiplier=2) as c1:
        with pytest.raises((ConnectionRefusedError, OSError)):
            c1.send("hei")


def test_successful_sending(unused_tcp_port):
    host = "localhost"
    url = f"ws://{host}:{unused_tcp_port}"
    messages = []
    mock_ws_thread = threading.Thread(
        target=partial(_mock_ws, messages=messages), args=(host, unused_tcp_port)
    )

    mock_ws_thread.start()
    messages_c1 = ["test_1", "test_2", "test_3", "stop"]

    with Client(url) as c1:
        for msg in messages_c1:
            c1.send(msg)

    mock_ws_thread.join()

    for msg in messages_c1:
        assert msg in messages


def test_retry(unused_tcp_port):
    host = "localhost"
    url = f"ws://{host}:{unused_tcp_port}"
    messages = []
    mock_ws_thread = threading.Thread(
        target=partial(_mock_ws, messages=messages, delay_startup=2),
        args=(
            host,
            unused_tcp_port,
        ),
    )

    mock_ws_thread.start()
    messages_c1 = ["test_1", "test_2", "test_3", "stop"]

    with Client(url, max_retries=2, timeout_multiplier=2) as c1:
        for msg in messages_c1:
            c1.send(msg)

    mock_ws_thread.join()

    for msg in messages_c1:
        assert msg in messages
