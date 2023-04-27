"""example class hierarchy for a complex state machine application"""
import threading
import time
import queue
import os
import platform
import gettext
import locale
import requests
import PySimpleGUI as sg
from abc import ABC, abstractmethod

FILE_DIR = os.path.join(os.path.dirname(__file__), "i18n")
FILE_NAME = os.path.split(__file__)[1].split(".")[0]

# Set initial locale
locale.setlocale(locale.LC_ALL, "")

gettext.bindtextdomain(FILE_NAME, FILE_DIR)
gettext.textdomain(FILE_NAME)
_ = gettext.gettext

sg.user_settings_filename(filename=FILE_NAME.join(".json"))


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
    def __init__(self, name, parent_machine):
        super().__init__(name, parent_machine)
        self.show_progress_bar = False

    def get_layout(self):
        # print("Getting layout for initial state")
        return [
            [sg.Text(_("Welcome to the complex state machine."))],
            [sg.ProgressBar(100, orientation="h", size=(36, 20), key="-progress_bar-", visible=self.show_progress_bar)],
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
        elif event == "-PROGRESS-":
            progress = values["-PROGRESS-"]
            if self.window:
                self.window["-progress_bar-"].update(progress,visible=True)
                if progress >= 100:
                    self.window["-progress_bar-"].update(0, visible=False)

            return None, None
        else:
            print(f"something else, maybe unexpected: {event}")
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
                icon="assets/tesseract-logo-houndstoothed-alpha.ico",
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


class HttpClient:
    """HTTP client Singleton"""

    _instance = None

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": f"Learning Python (0.1.0) {platform.system()}/{platform.release()}",
                "Accept-Language": locale.getlocale()[0],
            },
        )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HttpClient, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def get(self, url, timeout=5, **kwargs):
        """Send a GET request"""
        response = self.session.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    def post(self, url, timeout=5, **kwargs):
        """Send a POST request"""
        response = self.session.post(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    def close(self):
        """Close the HTTP session"""
        self.session.close()


class Task(ABC):
    """Abstract base class for tasks"""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback

    @abstractmethod
    def run(self):
        """Run the task instance"""


class SleepTask(Task):
    """Sleep task class inherits from Task, used for unit tests"""

    def __init__(self, seconds=4, progress_callback=None):
        super().__init__(progress_callback)
        self.seconds = seconds

    def run(self):
        print(f"Sleeping for {self.seconds} seconds")
        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            progress = (elapsed_time / self.seconds) * 100

            self.progress_callback(progress)
            if progress > 100:
                break


# class HttpGetTask(Task):
#     """Request task class inherits from Task, used for HTTP requests"""

#     def __init__(self, url, chunk_size=8192):
#         self.http_client = HttpClient()
#         self.url = url
#         self.chunk_size = chunk_size
#         self.content_length = 0
#         self.content_loaded = 0

#     def run(self):
#         response = self.http_client.get(self.url)
#         self.content_length = int(response.headers.get("Content-Length", 0))
#         self.content_loaded = 0


class DownloadManager:
    """Download manager / task queue class"""

    def __init__(self, num_workers=2, progress_callback=None):
        self.task_queue = queue.Queue()
        self.num_workers = num_workers
        self.progress_callback = progress_callback

    def set_progress_callback(self, progress_callback):
        """Set the progress callback"""
        self.progress_callback = progress_callback

    def add_task(self, task):
        """Add a task to the queue"""
        print(f"Adding task {task}")
        task.progress_callback = self.progress_callback  # set the callback
        self.task_queue.put(task)

    def worker(self):
        """Worker thread function"""
        while True:
            task = self.task_queue.get()
            print(f"Got task {task}")
            if task is None:
                print("Got None, breaking")
                break
            task.run()
            self.task_queue.task_done()

    def start(self):
        """Start a new worker thread"""
        threads = []
        for _ in range(self.num_workers):
            thread = threading.Thread(target=self.worker, daemon=True)
            thread.start()
            threads.append(thread)
            print(f"Started worker thread {thread.name}")

        return threads  # return the worker threads

    def stop(self):
        """Stop all worker threads"""
        for _ in range(self.num_workers):
            self.task_queue.put(None)


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
        self.download_manager.set_progress_callback(
            lambda progress: self.current_state.window.write_event_value(
                "-PROGRESS-", progress
            )
            if self.current_state.window is not None else None
        )
        worker_threads = self.download_manager.start()
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
                    print(f"Data: {data}")
                    try_task = SleepTask(10)
                    self.download_manager.add_task(try_task)
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
                        next_state_name, _ = secondary_window.transition_state(
                            event, values
                        )
                        if next_state_name is None:
                            secondary_window.close_window()
                            secondary_windows.remove(secondary_window)
                            break

        self.download_manager.stop()
        for thread in worker_threads:
            thread.join()


if __name__ == "__main__":
    state_machine = StateMachine()
    state_machine.run()
