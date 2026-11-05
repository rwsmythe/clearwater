"""Explicit GPU-pack requests, with byte progress delivered by the existing job runner (G9)."""

from __future__ import annotations

import time
from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clearwater import gpu_pack, gpu_pack_install
from clearwater.interfaces import JobResult, Progress

from .contract import JobHandle, JobRunner
from .messages import ascii_text

LICENSE_TEXT = (
    "GPU support downloads CuPy and NVIDIA's CUDA runtime libraries from PyPI into your user "
    "folder. The NVIDIA libraries are provided by NVIDIA under the NVIDIA Software License "
    "Agreement (the file `License.txt` in each NVIDIA package's `.dist-info` folder after the "
    "install); CuPy is MIT. Clearwater does not redistribute them."
)
"""The N13 statement shown before the user's download request."""

INSTALLED_TEXT = "GPU support is installed. Restart Clearwater to use it."
"""Completion text for a successfully published GPU pack."""


def _pack_job(operation: Callable[[], gpu_pack_install.PackResult]) -> JobResult:
    """Convert the non-Qt product outcome to IF-8; the worker holds no Qt object.

    The success message is carried in warnings because IF-8 has no success-text field.
    The GUI displays it as completion text, without a warning banner.
    """
    started = time.perf_counter()
    result = operation()
    return JobResult(
        ok=result.ok,
        outputs=(result.path,) if result.path is not None else (),
        warnings=(result.message,) if result.ok else (),
        failure=None if result.ok else result.message,
        device="unknown",
        elapsed_s=time.perf_counter() - started,
    )


def _install_job(progress: Progress) -> JobResult:
    """Run one transactional install; the closure captures only the structural progress."""
    return _pack_job(lambda: gpu_pack_install.install(progress))


def _remove_job(progress: Progress) -> JobResult:
    """Remove the calculated current pack on a worker, effective at the next start."""
    return _pack_job(gpu_pack_install.remove)


def _defer_remove_job(progress: Progress) -> JobResult:
    """Only mark removal of this process's loaded pack, without probing or renaming it."""
    return _pack_job(gpu_pack_install.defer_removal)


class GpuPackDialog(QDialog):
    """Window-modal install request and job status; opening it starts no download.

    Args:
        jobs: The shell's job runner.
        parent: The owning window.
    """

    busy_changed = Signal(bool)

    def __init__(self, jobs: JobRunner, parent: QWidget) -> None:
        """Build the plan, licence statement and explicit request button."""
        super().__init__(parent)
        self.setWindowTitle("Install GPU support")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(640, 620)
        self._jobs = jobs
        self._handle: JobHandle | None = None
        self._running = False
        layout = QVBoxLayout(self)
        self.plan_text = QPlainTextEdit(self)
        self.plan_text.setReadOnly(True)
        self.plan_text.setMinimumHeight(220)
        self.license_text = QLabel(LICENSE_TEXT, self)
        self.license_text.setTextFormat(Qt.TextFormat.PlainText)
        self.license_text.setWordWrap(True)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.current_wheel = QLabel(self)
        self.current_wheel.setTextFormat(Qt.TextFormat.PlainText)
        self.current_wheel.setWordWrap(True)
        self.status = QLabel(self)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.install_button = QPushButton("Download and install", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.install_button.clicked.connect(self._start)
        self.cancel_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.install_button)
        buttons.addWidget(self.cancel_button)
        for widget in (
            self.plan_text,
            self.license_text,
            self.progress_bar,
            self.current_wheel,
            self.status,
        ):
            layout.addWidget(widget)
        layout.addLayout(buttons)
        root = gpu_pack.pack_root()
        try:
            if root is None:
                raise ValueError("GPU support is not available on this platform")
            wanted = gpu_pack_install.plan()
            lines = [f"{wheel.name} {wheel.version}" for wheel in wanted.wheels]
            lines.extend(
                (
                    "",
                    f"Download: {wanted.download_size:,} bytes "
                    f"({wanted.download_size / (1 << 20):,.2f} MiB)",
                    f"Installed estimate: {wanted.installed_size:,} bytes "
                    f"({wanted.installed_size / (1 << 20):,.2f} MiB)",
                    f"Destination: {ascii_text(str(root / wanted.stamp))}",
                )
            )
            notice = gpu_pack_install.replacement_notice()
            if notice is not None:
                lines.extend(("", notice))
            self.plan_text.setPlainText("\n".join(lines))
        except ValueError as error:
            self.status.setText(ascii_text(str(error)))
            self.install_button.setEnabled(False)

    def _start(self) -> None:
        """Submit the user's request once; report and completion callbacks stay on Qt."""
        if self._running or not self.install_button.isEnabled():
            return
        self._running = True
        self.install_button.setEnabled(False)
        self.cancel_button.setText("Cancel")
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.current_wheel.clear()
        self.status.setText("Downloading GPU support...")
        self.busy_changed.emit(True)
        try:
            self._handle = self._jobs.run(
                _install_job, on_done=self._done, on_progress=self._progress
            )
        except RuntimeError as error:
            self._done(JobResult(False, (), (), str(error), "unknown", 0))

    def _progress(self, done: int, total: int | None, message: str) -> None:
        """Scale byte counts to a bounded Qt integer range; retain the current wheel name."""
        self.progress_bar.setValue(min(1000, max(0, done * 1000 // total)) if total else 0)
        self.current_wheel.setText(ascii_text(message))

    def _done(self, result: JobResult) -> None:
        """Show the shared outcome only after the worker has finished its cleanup."""
        self._running = False
        self._handle = None
        text = (
            (result.warnings[0] if result.warnings else INSTALLED_TEXT)
            if result.ok
            else (result.failure or "GPU support installation failed")
        )
        self.status.setText(ascii_text(text))
        self.install_button.setEnabled(not result.ok)
        self.cancel_button.setText("Close")
        self.cancel_button.setEnabled(True)
        if result.ok:
            self.progress_bar.setValue(1000)
        self.busy_changed.emit(False)

    def reject(self) -> None:
        """Cancel an active job and keep its dialog alive until cleanup; otherwise close."""
        if self._running:
            if self._handle is not None:
                self._handle.cancel()
            self.cancel_button.setEnabled(False)
            self.status.setText("Cancelling GPU support installation...")
            return
        super().reject()
