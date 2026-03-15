"""
utils/thread_worker.py

Runs any scan or clean operation on a background thread so the UI
never freezes. Uses Python's threading module — lightweight and simple.

Pattern:
    worker = ThreadWorker(
        task=my_scan_function,        # the function to run
        args=(path, recursive),       # its arguments
        on_result=handle_results,     # called on the main thread when done
        on_error=handle_error,        # called if an exception is raised
        on_progress=update_progress,  # optional — called during the task
    )
    worker.start()
    # worker.cancel()  ← call this to request early stop

Your task function receives a 'cancel_event' keyword argument automatically.
Check it periodically if your task runs long:

    def my_scan(path, cancel_event=None):
        for item in big_list:
            if cancel_event and cancel_event.is_set():
                return []   # stopped early
            # ... do work
"""

import threading
from typing import Callable, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ThreadWorker:
    """
    Wraps a long-running function in a daemon thread.
    Safe to use from CustomTkinter — callbacks are scheduled
    via the CTk widget's after() so they run on the main thread.
    """

    def __init__(
        self,
        task: Callable,
        args: tuple = (),
        kwargs: dict = None,
        on_result: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_done: Optional[Callable[[], None]] = None,
        ui_widget=None,  # a CTk widget used to schedule callbacks via .after()
    ):
        self.task        = task
        self.args        = args
        self.kwargs      = kwargs or {}
        self.on_result   = on_result
        self.on_error    = on_error
        self.on_progress = on_progress
        self.on_done     = on_done
        self.ui_widget   = ui_widget

        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.is_running = False

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        """Start the background task. No-op if already running."""
        if self.is_running:
            logger.warning("ThreadWorker.start() called while already running")
            return

        self._cancel_event.clear()
        self.is_running = True

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,   # dies automatically if the app closes
        )
        self._thread.start()
        logger.debug(f"ThreadWorker started: {self.task.__name__}")

    def cancel(self):
        """Request the task to stop. The task must check cancel_event itself."""
        if self.is_running:
            logger.info(f"Cancelling worker: {self.task.__name__}")
            self._cancel_event.set()

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self):
        """Runs on the background thread."""
        try:
            result = self.task(
                *self.args,
                **self.kwargs,
                cancel_event=self._cancel_event,
            )
            self._dispatch(self.on_result, result)

        except Exception as e:
            logger.error(
                f"ThreadWorker error in {self.task.__name__}: {e}",
                exc_info=True,
            )
            self._dispatch(self.on_error, e)

        finally:
            self.is_running = False
            self._dispatch(self.on_done)
            logger.debug(f"ThreadWorker finished: {self.task.__name__}")

    def _dispatch(self, callback: Optional[Callable], *args):
        """
        Call a callback safely on the main thread.
        If a CTk widget was supplied, use .after(0, ...).
        Otherwise call directly (fine for non-UI callbacks).
        """
        if callback is None:
            return

        if self.ui_widget:
            try:
                self.ui_widget.after(0, lambda: callback(*args))
            except Exception:
                # Widget may have been destroyed
                pass
        else:
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Callback error: {e}", exc_info=True)


# ── Convenience function ──────────────────────────────────────────────────────

def run_in_background(
    task: Callable,
    args: tuple = (),
    kwargs: dict = None,
    on_result: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    on_done: Optional[Callable] = None,
    ui_widget=None,
) -> ThreadWorker:
    """
    One-liner helper for fire-and-forget background tasks.

    Usage:
        run_in_background(
            task=scan_temp_folder,
            args=("C:\\Windows\\Temp",),
            on_result=self.show_results,
            on_error=self.show_error,
            ui_widget=self,
        )
    """
    worker = ThreadWorker(
        task=task,
        args=args,
        kwargs=kwargs,
        on_result=on_result,
        on_error=on_error,
        on_done=on_done,
        ui_widget=ui_widget,
    )
    worker.start()
    return worker