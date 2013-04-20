import os
import threading
import SimpleHTTPServer
import BaseHTTPServer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class EventHandler(FileSystemEventHandler):
    """Watches all files except those that are hidden or are in
    the hidden directory.
    """

    def __init__(self, project_dir, new_changes_event):
        """
        :param project_dir: project directory being watched
        :param new_changes_event: event to be set when changes occur
        :type new_changes_event: :class:`threading.Event`
        """
        self._project_dir = project_dir
        self._new_changes_event = new_changes_event
        super(EventHandler, self).__init__()

    def on_any_event(self, event):
        path = os.path.realpath(event.src_path)
        rel_path = os.path.relpath(path, self._project_dir)

        rest = rel_path
        while rest:
            rest, head = os.path.split(rest)
            if head.startswith('.'):
                return

        self._new_changes_event.set()


class Shutdowner(threading.Thread):
    """Daemon thread that waits for the changes and then
    shuts down the server.
    """

    def __init__(self, http_server, new_changes_event):
        """
        :param http_server: server to be shut down
        :type http_server: :class:`BaseHTTPServer.HTTPServer`
        :param new_changes_event: event to be listened to
        :type new_changes_event: :class:`threading.Event`
        """
        super(Shutdowner, self).__init__()
        self.daemon = True
        self._http_server = http_server
        self._new_changes_event = new_changes_event

    def run(self):
        while True:
            self._new_changes_event.wait()
            self._http_server.shutdown()
            self._new_changes_event.clear()


def serve(host='localhost', port=8000):
    """Runs the development server at given `host` and `port`,
    watches the changes and regenerates the site.
    """
    http_server = BaseHTTPServer.HTTPServer(
        (host, port), SimpleHTTPServer.SimpleHTTPRequestHandler)

    # Event to be set when the project has changes and needs to be rebuilt
    new_changes_event = threading.Event()

    # Both `shutdowner` and `observer` are daemon threads
    shutdowner = Shutdowner(http_server, new_changes_event)
    shutdowner.start()

    observer = Observer()
    observer.start()

    project_dir = os.getcwd()
    www_dir = os.path.join(project_dir, 'www')
    event_handler = EventHandler(project_dir, new_changes_event)
    observer.schedule(event_handler, path=project_dir, recursive=True)

    from carcade.cli import build  # To resolve a circular import
    while True:
        os.chdir(project_dir)
        build(to=www_dir, atomically=True)
        if not os.path.exists(www_dir):
            return 1
        os.chdir(www_dir)

        http_server.serve_forever()
