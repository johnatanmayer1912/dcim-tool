"""Cancel must close in-flight SSH sockets, not only set a cooperative flag."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.task_control_plane import (
    bind_session_key,
    register_live_connection,
    register_task,
    request_cancel,
    request_session_cancel,
)


class _FakeRemote:
    def __init__(self):
        self.closed = False
        self.transport_closed = False

    def close(self):
        self.closed = True

    def get_transport(self):
        class _T:
            def __init__(self, parent):
                self._parent = parent

            def close(self):
                self._parent.transport_closed = True

        return _T(self)


class _FakeConn:
    def __init__(self):
        self.disconnected = False
        self.remote_conn = _FakeRemote()

    def disconnect(self):
        self.disconnected = True


class TestSshCancelDisconnect(unittest.TestCase):
    def test_request_session_cancel_closes_socket(self):
        conn = _FakeConn()
        bind_session_key('job-ssh-1')
        register_live_connection(conn, 'job-ssh-1')
        n = request_session_cancel('job-ssh-1')
        self.assertGreaterEqual(n, 1)
        self.assertTrue(conn.disconnected)
        self.assertTrue(conn.remote_conn.closed)

    def test_request_cancel_disconnects_registered_task(self):
        conn = _FakeConn()
        tid = register_task('qa_ssh_kill', label='qa')
        register_live_connection(conn, tid)
        self.assertTrue(request_cancel(tid))
        self.assertTrue(conn.disconnected)


if __name__ == '__main__':
    unittest.main()
