"""Demo using async/await with asyncio + PySimpleGUI"""
import asyncio

# import aiohttp
# import aiofiles
import logging
from abc import ABC, abstractmethod
from typing import Callable, Any
import PySimpleGUI as sg


class WindowState(ABC):
    """Abstract class for window states."""

    @abstractmethod
    def window_layout(self):
        """Return the window layout."""

    @abstractmethod
    def handle_event(self, event, values, window):
        """Handle window-specific events."""

    @abstractmethod
    def update_window(self, values, window):
        """Update the window layout."""


class TabbedMainWindow(WindowState):
    """Window state for the tabbed main window."""

    def window_layout(self):
        return [
            [
                sg.TabGroup(
                    [
                        [
                            sg.Tab("Installer", self.installer_tab()),
                            sg.Tab("Downloader", self.downloader_tab()),
                            sg.Tab("Debugger", self.debugger_tab()),
                        ]
                    ],
                    expand_x=True,
                    expand_y=True,
                )
            ],
        ]

    def installer_tab(self):
        """Return the layout for the installer tab."""
        return [
            [sg.Text("Installer Tab")],
            [sg.Button("Install")],
            [sg.Button("Popout Installer", key="-POPOUT_INSTALLER-")],
        ]

    def downloader_tab(self):
        """Return the layout for the downloader tab."""
        return [
            [sg.Text("Downloader Tab")],
            [sg.Button("Download")],
        ]

    def debugger_tab(self):
        """Return the layout for the debugger tab."""
        return [
            [sg.Text("A typical PSG application")],
            [sg.Input(key="-IN-")],
            [sg.Text(" ", key="-OUT-", size=(45, 1))],
            [sg.CBox("Checkbox 1"), sg.CBox("Checkbox 2")],
            [
                sg.Radio("a", 1, key="-R1-"),
                sg.Radio("b", 1, key="-R2-"),
                sg.Radio("c", 1, key="-R3-"),
            ],
            [sg.Combo(["c1", "c2", "c3"], size=(6, 3), key="-COMBO-")],
            [sg.Output(size=(50, 6))],
            [
                sg.Ok(),
                sg.Exit(),
                sg.Button("Enable"),
                sg.Button("Popout"),
                sg.Button("Debugger"),
                sg.Debug(key="Buggon"),
            ],
        ]

    def popout_installer_tab(self, main_window):
        """Popout the installer tab."""
        layout = self.installer_tab()
        popout_window = sg.Window(
            "Installer",
            layout,
            size=(800, 600),
            icon="assets/tesseract-logo-houndstoothed-alpha.ico",
            titlebar_icon="assets/tesseract-logo-houndstoothed-alpha.ico",
        )
        main_window["Installer"].update(visible=False)

        while True:
            event, _values = popout_window.read(timeout=100)
            if event in (sg.WIN_CLOSED, "Exit"):
                break

        main_window["Installer"].update(visible=True)
        popout_window.close()

    def handle_event(self, event, values, window):
        """Handle window-specific events."""
        match event:
            case "-POPOUT_INSTALLER-":
                self.popout_installer_tab(window)
            case "Enable":
                window.enable_debugger()
            case "Popout":
                sg.show_debugger_popout_window()
            case "Buggon":
                sg.show_debugger_popout_window()
            case "Debugger":
                sg.show_debugger_window()

    def update_window(self, values, window):
        """Update the window layout."""
        window["-OUT-"].update(values["-IN-"])


class AppState:
    """Application state: contains and mutates states."""

    def __init__(self):
        self.window_state = None
        self.window_states = {}

    def register_window_state(self, state_name, window_state):
        """Register a window state."""
        self.window_states[state_name] = window_state

    def set_window_state(self, state_name):
        """Set the window state."""
        self.window_state = self.window_states[state_name]

    def run(self):
        """Run the application."""
        layout = self.window_state.window_layout()
        window = sg.Window(
            "Demo App",
            layout,
            size=(800, 600),
            debugger_enabled=False,
            icon="assets/tesseract-logo-houndstoothed-alpha.ico",
            titlebar_icon="assets/tesseract-logo-houndstoothed-alpha.ico",
        )

        counter = 0

        while True:
            event, values = window.read(timeout=100)
            if event in (sg.WIN_CLOSED, "Exit"):
                break

            self.window_state.handle_event(event, values, window)
            self.window_state.update_window(values, window)

            counter += 1

        window.close()


class Task:
    """A task that can be run, paused, and resumed."""

    def __init__(self, coro: Callable[..., Any], *args, **kwargs):
        self.coro = coro
        self.args = args
        self.kwargs = kwargs
        self._task = None

    async def run(self):
        """Run by calling asyncio.create_task() on the coro."""
        logging.debug(self)
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self.coro(*self.args, **self.kwargs))
        await self._task

    def cancel(self):
        """Cancels the task."""
        if self._task:
            self._task.cancel()

    def pause(self):
        """Pause a task."""

    def resume(self):
        """Resume a task."""


class TaskQueue:
    """A queue of tasks that can be run."""

    def __init__(self):
        self.queue = asyncio.Queue()

    async def add_task(self, task: Task):
        """Add a task to the queue."""
        await self.queue.put(task)

    async def run_tasks(self):
        """Run all tasks in the queue."""
        while True:
            task = await self.queue.get()
            if task:
                print(f"run_tasks(): {task}")
                await task.run()
            self.queue.task_done()


class PauseResumeTask(Task):
    """A test case task that can be paused and resumed."""

    def __init__(self, coro, *args, **kwargs):
        super().__init__(coro, *args, **kwargs)
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    async def _coro_wrapper(self, *args, **kwargs):
        while not self._task.done():
            self._pause_event.clear()
            try:
                await self.coro(*args, **kwargs)
            except asyncio.CancelledError:
                break
            await self._pause_event.wait()

    async def run(self):
        if not self._task or self._task.done():
            self._task = asyncio.create_task(
                self._coro_wrapper(*self.args, **self.kwargs)
            )
        await self._task

    def pause(self):
        print(f"pause(): {self}")
        self._pause_event.clear()

    def resume(self):
        print(f"resume(): {self}")
        self._pause_event.set()


async def main():
    """Execution entry point."""
    app_state = AppState()
    app_state.register_window_state("TabbedWindow", TabbedMainWindow())
    app_state.set_window_state("TabbedWindow")
    app_state.run()


asyncio.run(main())
