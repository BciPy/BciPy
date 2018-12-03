from bcipy.acquisition.processor import Processor

import subprocess
import os
import signal

import time


class ViewerProcessor(Processor):
    """Processor that displays the streaming data in a GUI."""

    def __init__(self):
        super(ViewerProcessor, self).__init__()
        self.viewer = 'bcipy/gui/viewer/data_viewer.py'
        self.started = False

    # @override ; context manager
    def __enter__(self):
        self._check_device_info()

        # https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true
        cmd = f'python {self.viewer}'
        self.subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        shell=True, preexec_fn=os.setsid)
        # hack: wait for window to open, so it doesn't error out when the main
        # window is open fullscreen.
        time.sleep(2)
        self.started = True
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        os.killpg(os.getpgid(self.subproc.pid), signal.SIGTERM)
        self.started = False

    def process(self, record, timestamp=None):
        pass
