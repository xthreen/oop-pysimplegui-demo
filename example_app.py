"""example class hierarchy for a complex state machine application"""
import threading
import queue
import time
import os
import gettext
import locale
import requests
import PySimpleGUI as sg

FILE_DIR = os.path.join(os.path.dirname(__file__), "i18n")
FILE_NAME = os.path.split(__file__)[1].split(".")[0]

# Set locale
locale.setlocale(locale.LC_ALL, "")

gettext.bindtextdomain(FILE_NAME, FILE_DIR)
gettext.textdomain(FILE_NAME)
_ = gettext.gettext

sg.user_settings_filename(filename=FILE_NAME.join(".json"))


# Fetch JSON data function
def fetch_json(url):
    """Fetch JSON data from the given URL"""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        json_data = response.json()
        return json_data, None
    except requests.exceptions.RequestException as fetch_error:
        return None, str(fetch_error)


# State classes
class State:
    """Base class for all states"""

    def __init__(self, name, parent_machine):
        self.name = name
        self.window = None
        self.parent_machine = parent_machine

    def get_layout(self):
        """Return the layout for the state"""
        raise NotImplementedError("This method must be implemented in the subclass")

    def transition_state(self, event, values, secondary_windows=None):
        """Return the next state to transition to"""
        raise NotImplementedError("This method must be implemented in the subclass")

    def open_window(self):
        """Open the window"""
        # print(f"Opening {self.name} window")
        if not self.window:
            self.window = sg.Window(
                f"{self.name.capitalize()} State",
                self.get_layout(),
                icon="assets/tesseract-logo-houndstoothed-alpha.ico",
                titlebar_icon="assets/tesseract-logo-houndstoothed-alpha.ico",
                finalize=True,
            )

    def close_window(self):
        """Close the window"""
        # print(f"Closing {self.name} window")
        if self.window:
            self.window.close()
            self.window = None


class InitialState(State):
    """Initial state"""

    def get_layout(self):
        # print("Getting layout for initial state")
        return [
            [sg.Text(_("Welcome to the complex state machine."))],
            [
                sg.Button(_("Go to State A"), key="-go_to_state_a-"),
                sg.Button(_("Go to State B"), key="-go_to_state_b-"),
                sg.Button(_("Go to State C"), key="-go_to_state_c-"),
                sg.Button(_("Exit"), key="-exit-"),
            ],
            [sg.Text(_("Enter the file URL to download:"))],
            [sg.InputText(key="file_url"), sg.Button(_("Download"), key="-download-")],
        ]

    def transition_state(self, event, values, secondary_windows=None):
        """Transition to the next state based on the event and values"""
        data = None
        if event == "-go_to_state_a-":
            next_state_name = "state_a"
        elif event == "-go_to_state_b-":
            next_state_name = "state_b"
        elif event == "-go_to_state_c-":
            self.parent_machine.states["state_c"].open_window()
            if secondary_windows is not None:
                secondary_windows.append(self.parent_machine.states["state_c"])
            return None, None
        elif event == "-download-":
            file_url = values["file_url"]
            if file_url:
                next_state_name = "download"
                data = file_url
        else:
            next_state_name = self.name
        return next_state_name, data


class StateA(State):
    """Example State A"""

    def __init__(self, name, parent_machine):
        super().__init__(name, parent_machine)
        self.window = None

    def get_layout(self):
        return [
            [sg.Text(_("You are in State A."))],
            [
                sg.Button(_("Go to State B"), key="-go_to_state_b-"),
                sg.Button(_("Go back to Initial"), key="-go_to_initial-"),
                sg.Button(_("Exit"), key="-exit-"),
            ],
        ]

    def open_window(self):
        """Open the window"""
        self.window = sg.Window("State A", self.get_layout(), finalize=True)

    def close_window(self):
        """Close the window"""
        self.window.close()
        self.window = None

    def transition_state(self, event, values, secondary_windows=None):
        data = None
        if event == "-go_to_state_b-":
            next_state_name = "state_b"
        elif event == "-go_to_initial-":
            next_state_name = "initial"
        else:
            next_state_name = self.name
        return next_state_name, data


class StateB(State):
    """Example State B"""

    def __init__(self, name, parent_machine):
        super().__init__(name, parent_machine)
        self.window = None

    def get_layout(self):
        return [
            [sg.Text(_("You are in State B."))],
            [
                sg.Button(_("Go to State A"), key="-go_to_state_a-"),
                sg.Button(_("Go back to Initial"), key="-go_to_initial-"),
                sg.Button(_("Exit"), key="-exit-"),
            ],
        ]

    def transition_state(self, event, values, secondary_windows=None):
        data = None
        if event == "-go_to_state_a-":
            next_state_name = "state_a"
        elif event == "-go_to_initial-":
            next_state_name = "initial"
        else:
            next_state_name = self.name
        return next_state_name, data


class StateC(State):
    """Example State C, secondary window"""

    def get_layout(self):
        return [
            [sg.Text(_("You are in State C."))],
            [sg.Button(_("Close the State C window"), key="-close_state_c-")],
        ]

    def open_window(self):
        """Open the window"""
        if not self.window:
            self.window = sg.Window(
                f"{self.name.capitalize()} State",
                self.get_layout(),
                no_titlebar=True,
                grab_anywhere_using_control=True,
                icon="assets/tesseract-logo-houndstoothed-alpha.ico",
                titlebar_icon="assets/tesseract-logo-houndstoothed-alpha.ico",
                relative_location=(128, 144),
                finalize=True,
            )
            self.window.bring_to_front()

    def transition_state(self, event, values, secondary_windows=None):
        # print(f"StateC transition_state called with event {event}")
        next_state_name = self.name
        data = None
        if event == "-close_state_c-":
            # print("Closing State C window")
            next_state_name = None
            self.close_window()
        return next_state_name, data


# DownloadManager class
class DownloadManager:
    """Download manager / task queue class"""

    def __init__(self):
        self.task_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def worker(self):
        """Worker thread function"""
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            self.download_file(task)
            self.task_queue.task_done()

    def download_file(self, file_url):
        """Download the file at the given URL"""
        print(f"Downloading file: {file_url}")
        time.sleep(5)  # Simulate a long-running task
        print(f"Download complete: {file_url}")
        return True

    def add_task(self, file_url):
        """Add a task to the queue"""
        self.task_queue.put(file_url)

    def stop(self):
        """Stop the worker thread"""
        self.task_queue.put(None)


# StateMachine class
class StateMachine:
    """State machine class"""

    def __init__(self):
        self.states = {
            "initial": InitialState("initial", self),
            "state_a": StateA("state_a", self),
            "state_b": StateB("state_b", self),
            "state_c": StateC("state_c", self),
        }
        self.current_state = self.states["initial"]
        self.download_manager = DownloadManager()

    def update_user_settings(self, values):
        """Update the user settings"""
        print(f"Updating user settings: {values}")
        return sg.user_settings_save()

    def run(self):
        """Run the state machine"""
        self.current_state.open_window()
        secondary_windows = []  # Secondary window container list
        while True:
            # Read the from all open windows
            window, event, values = sg.read_all_windows()
            # print(
            #     f"window={window}, event={event}, secondary_windows={secondary_windows}"
            # )
            if window == self.current_state.window:
                if event == sg.WIN_CLOSED or event == "-exit-":
                    break

                # Get the next state name and data based on the event and values
                next_state_name, data = self.current_state.transition_state(
                    event, values, secondary_windows
                )

                # Check if the next state name is "download"
                if next_state_name == "download":
                    self.download_manager.add_task(data)
                elif next_state_name == "state_c":
                    secondary_windows.append(self.states[next_state_name])
                    self.states[next_state_name].open_window()
                    self.states[next_state_name].window.bring_to_front()
                elif next_state_name in self.states:
                    self.current_state.close_window()
                    self.current_state = self.states[next_state_name]
                    self.current_state.open_window()
            elif any(window == state.window for state in secondary_windows):
                for secondary_window in secondary_windows[:]:
                    if window == secondary_window.window:
                        next_state_name, _ = secondary_window.transition_state(event, values)
                        if next_state_name is None:
                            secondary_window.close_window()
                            secondary_windows.remove(secondary_window)
                            break

        self.download_manager.stop()


if __name__ == "__main__":
    state_machine = StateMachine()
    state_machine.run()
