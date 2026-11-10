"""A running server must never silently mask the updated application."""

import contextlib
import io
import socket
import unittest
from unittest.mock import patch
from server.__main__ import main


class StartupTests(unittest.TestCase):
    def test_occupied_port_has_actionable_error_without_starting_server(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            port = occupied.getsockname()[1]
            message = io.StringIO()
            with (
                patch("sys.argv", ["server", "--port", str(port)]),
                patch("server.__main__.uvicorn.run") as run,
            ):
                with contextlib.redirect_stderr(message), self.assertRaises(SystemExit) as error:
                    main()
                self.assertEqual(error.exception.code, 2)
                self.assertIn("bereits belegt", message.getvalue())
                run.assert_not_called()
