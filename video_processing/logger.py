import re
from flask_socketio import emit
import queue


class MoviePyLogger:
    def __init__(self):
        self.progress_queue = queue.Queue()

    def custom_stdout_write(self, s) -> int:
        self.progress_queue.put(s)

        percentage_pattern = r"(\d+)\%"
        percentage_match = re.search(percentage_pattern, s)
        if percentage_match is not None:
            percentage = int(percentage_match.group(1))
            emit("progress", {"progress": percentage}, broadcast=True)
        self.progress_queue.task_done()
        return 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.progress_queue.join()
