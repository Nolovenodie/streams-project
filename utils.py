import time
import hashlib
import threading
import subprocess

from ffmpeg_streaming._process import Process, _p_open
from ffmpeg_streaming._utiles import get_time, time_left


class CommandProcess(object):
    def __init__(self, command, monitor):
        print(command)
        options = {
            "stdin": None,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "universal_newlines": False
        }
        self.process = _p_open(command, **options)
        self.monitor = monitor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.process.kill()

    def _monitor(self):
        duration = 1
        _time = 0
        log = []
        start_time = time.time()

        while True:
            line = self.process.stdout.readline().strip()
            if line == '' and self.process.poll() is not None:
                break

            if line != '':
                log += [line]

            if callable(self.monitor):
                self.monitor(line)
                # duration = get_time('Duration: ', line, duration)
                # _time = get_time('time=', line, _time)
                # self.monitor(line, duration, _time, time_left(start_time, _time, duration), self.process)

        Process.out = log

    def _thread_mon(self):
        thread = threading.Thread(target=self._monitor)
        thread.start()

        thread.join()
        if thread.is_alive():
            self.process.terminate()
            thread.join()
            raise RuntimeError('Timeout! exceeded the timeout of {} seconds.'.format(str(self.timeout)))

    def run(self):
        self._thread_mon()

        if self.process.poll():
            error = str(Process.err) if Process.err else str(Process.out)
            raise RuntimeError('failed to execute command: ', error)
        return Process.out, Process.err


def md5(data):
    return hashlib.md5(data.encode("utf-8")).hexdigest()
