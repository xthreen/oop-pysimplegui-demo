"""Unit tests for example_app.py."""
import unittest
from unittest.mock import patch
from example_app import (
    InitialState,
    StateA,
    StateB,
    StateC,
    DownloadManager,
    StateMachine,
)


BASE_URL = "https://www.example.com"


class TestInitialState(unittest.TestCase):
    """Unit tests for InitialState class."""

    def setUp(self):
        self.parent_machine = StateMachine()
        self.state = InitialState("initial", self.parent_machine)

    def test_get_layout(self):
        """Test get_layout method."""
        layout = self.state.get_layout()
        self.assertTrue(len(layout) > 0)

    def test_transition_state(self):
        """Test transition_state method."""
        test_cases = [
            ("-go_to_state_a-", "state_a"),
            ("-go_to_state_b-", "state_b"),
            ("-go_to_state_c-", None),
            ("-exit-", "initial"),
        ]
        for event, expected_next_state_name in test_cases:
            next_state_name, _data = self.state.transition_state(
                event, {"file_url": ""}
            )
            self.assertEqual(next_state_name, expected_next_state_name)


class TestStateA(unittest.TestCase):
    """Unit tests for StateA class."""

    def setUp(self):
        self.parent_machine = StateMachine()
        self.state = StateA("state_a", self.parent_machine)

    def test_get_layout(self):
        """Test get_layout method."""
        layout = self.state.get_layout()
        self.assertTrue(len(layout) > 0)

    def test_transition_state(self):
        """Test transition_state method."""
        test_cases = [
            ("-go_to_state_b-", "state_b"),
            ("-go_to_initial-", "initial"),
            ("-exit-", "state_a"),
        ]
        for event, expected_next_state_name in test_cases:
            next_state_name, _data = self.state.transition_state(
                event, {"file_url": ""}
            )
            self.assertEqual(next_state_name, expected_next_state_name)


class TestStateB(unittest.TestCase):
    """Unit tests for StateB class."""

    def setUp(self):
        self.parent_machine = StateMachine()
        self.state = StateB("state_b", self.parent_machine)

    def test_get_layout(self):
        """Test get_layout method."""
        layout = self.state.get_layout()
        self.assertTrue(len(layout) > 0)

    def test_transition_state(self):
        """Test transition_state method."""
        test_cases = [
            ("-go_to_state_a-", "state_a"),
            ("-go_to_initial-", "initial"),
            ("-exit-", "state_b"),
        ]
        for event, expected_next_state_name in test_cases:
            next_state_name, _data = self.state.transition_state(
                event, {"file_url": ""}
            )
            self.assertEqual(next_state_name, expected_next_state_name)


class TestStateC(unittest.TestCase):
    """Unit tests for StateC class."""

    def setUp(self):
        self.parent_machine = StateMachine()
        self.state = StateC("state_c", self.parent_machine)

    def test_get_layout(self):
        """Test get_layout method."""
        layout = self.state.get_layout()
        self.assertTrue(len(layout) > 0)

    def test_transition_state(self):
        """Test transition_state method."""
        test_cases = [
            ("-close_state_c-", None),
        ]
        for event, expected_next_state_name in test_cases:
            next_state_name, _data = self.state.transition_state(
                event, {"file_url": ""}
            )
            self.assertEqual(next_state_name, expected_next_state_name)


class TestDownloadManager(unittest.TestCase):
    """Unit tests for DownloadManager class."""

    def setUp(self):
        self.download_manager = DownloadManager()

    @patch("example_app.DownloadManager.download_file")
    def test_add_task(self, mock_download_file):
        """Test add_task method."""
        mock_download_file.return_value = True

        valid_file_url = BASE_URL.join("example.txt")
        self.download_manager.add_task(valid_file_url)

        self.download_manager.task_queue.join()

        mock_download_file.assert_called_once_with(valid_file_url)

    @patch("example_app.DownloadManager.download_file")
    def test_download_file(self, mock_download_file):
        """Test download_file method."""
        valid_file_url = BASE_URL.join("example.txt")

        mock_download_file.return_value = True
        result = self.download_manager.download_file(valid_file_url)
        self.assertTrue(result)

        invalid_file_url = "teh_heckz_this_is_not_a_valid_url"
        mock_download_file.return_value = False
        result = self.download_manager.download_file(invalid_file_url)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
