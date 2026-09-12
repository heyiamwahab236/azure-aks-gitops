"""Run with python inside each worker image; no live dependencies used."""
import socket
from unittest.mock import Mock, patch

from fastapi import HTTPException
from app import main


class StopTest(BaseException):
    pass


connection = Mock()
channel = connection.channel.return_value


def consuming():
    assert main.ready() == {"status": "ready"}
    raise StopTest()


def disconnected(_):
    assert not main.consumer_ready.is_set()
    try:
        main.ready()
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("Disconnected worker reported ready")


channel.start_consuming.side_effect = consuming
with patch.object(main.pika, "BlockingConnection", side_effect=[socket.gaierror(-3, "DNS unavailable"), connection]) as connect, patch.object(main.time, "sleep", side_effect=disconnected):
    try:
        main.consume()
    except StopTest:
        pass
    assert connect.call_count == 2
    connection.close.assert_called_once()
    assert not main.consumer_ready.is_set()
print("PASS: DNS retry, readiness transitions, and connection cleanup")
