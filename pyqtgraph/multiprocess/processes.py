"""Multiprocess helpers — disabled in the opencratertool QGIS plugin build."""

from .remoteproxy import ClosedError, NoResultError

__all__ = ['Process', 'QtProcess', 'ForkedProcess', 'ClosedError', 'NoResultError']


class Process:
    """Disabled: upstream uses subprocess + pickle IPC unused by this plugin."""

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "pyqtgraph.multiprocess.Process is disabled in the opencratertool "
            "QGIS plugin build for security reasons"
        )


class QtProcess(Process):
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "pyqtgraph.multiprocess.QtProcess is disabled in the opencratertool "
            "QGIS plugin build for security reasons"
        )


class ForkedProcess:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "pyqtgraph.multiprocess.ForkedProcess is disabled in the opencratertool "
            "QGIS plugin build for security reasons"
        )
