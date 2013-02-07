import os
import threading
import SimpleHTTPServer
import BaseHTTPServer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


PROJECT_DIR = os.getcwd()


class EventHandler(FileSystemEventHandler):
    """Watches all files except those that are hidden or are in
    the hidden directory.
    """

    def __init__(self, new_changes_event):
        """
        :param new_changes_event: event to be set when changes occur
        :type new_changes_event: :class:`threading.Event`
        """
        self._new_changes_event = new_changes_event
        super(EventHandler, self).__init__()

    def on_any_event(self, event):
        path = os.path.realpath(event.src_path)

        # If file isn't hidden
        if not os.path.basename(path).startswith('.'):
            self._new_changes_event.set()


class Builder(threading.Thread):
    """Daemon thread that waits for the changes and then shuts down the server.
    """

    def __init__(self, http_server, new_changes_event):
        """
        :param http_server: server to be shut down
        :type http_server: :class:`BaseHTTPServer.HTTPServer`
        :param new_changes_event: event to be listened to
        :type new_changes_event: :class:`threading.Event`
        """
        super(Builder, self).__init__()
        self.daemon = True
        self._http_server = http_server
        self._new_changes_event = new_changes_event

    def run(self):
        while True:
            self._new_changes_event.wait()
            self._http_server.shutdown()
            self._new_changes_event.clear()


def main():
    http_server = BaseHTTPServer.HTTPServer(
        ('', 8000), SimpleHTTPServer.SimpleHTTPRequestHandler)

    # Event to be set when the project has changes and needs to be rebuilt
    new_changes_event = threading.Event()

    # Both `builder` and `observer` are daemon threads
    builder = Builder(http_server, new_changes_event)
    builder.start()

    observer = Observer()
    observer.start()

    www_dir = os.path.join(PROJECT_DIR, 'www')
    event_handler = EventHandler(new_changes_event)

    while True:
        os.chdir(PROJECT_DIR)
        try:
            from carcade.cli import build  # Circular import
            build(www_dir)
            os.chdir(www_dir)
        except Exception as e:
            print 'Ooops...', e

        watch = observer.schedule(event_handler, path=PROJECT_DIR, recursive=True)
        http_server.serve_forever()
        # Disable observer during build time due to the bugs in watchdog
        observer.unschedule(watch)
