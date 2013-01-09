import os
import threading
import SimpleHTTPServer
import BaseHTTPServer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from build import sh


PROJECT_DIR = os.getcwd()


class EventHandler(FileSystemEventHandler):
    def __init__(self, new_changes_event):
        self._new_changes_event = new_changes_event
        super(EventHandler, self).__init__()

    def on_any_event(self, event):
        # Note: `www` is symlink to `.build-*`
        path = os.path.realpath(event.src_path)
        rel_path = os.path.relpath(path, PROJECT_DIR)

        # If file isn't hidden and isn't in a hidden directory
        if not (os.path.basename(path).startswith('.') or
                rel_path.startswith('.')):
            self._new_changes_event.set()


class Builder(threading.Thread):
    def __init__(self, http_server, new_changes_event):
        super(Builder, self).__init__()
        self.daemon = True
        self._http_server = http_server
        self._new_changes_event = new_changes_event

    def run(self):
        while True:
            self._new_changes_event.wait()
            sh('cd %s && carcade build' % PROJECT_DIR)
            self._new_changes_event.clear()
            self._http_server.shutdown()


def main():
    http_server = BaseHTTPServer.HTTPServer(
        ('', 8000), SimpleHTTPServer.SimpleHTTPRequestHandler)

    # Event is set when the project has changes and needs to be rebuilt
    new_changes_event = threading.Event()

    builder = Builder(http_server, new_changes_event)

    observer = Observer()
    event_handler = EventHandler(new_changes_event)
    observer.schedule(event_handler, path='.', recursive=True)

    # Both `builder` and `observer` are daemon threads
    builder.start()
    observer.start()

    www_dir = os.path.join(PROJECT_DIR, 'www')
    if not os.path.exists(www_dir):
        sh('cd %s && carcade build' % PROJECT_DIR)

    while True:
        os.chdir(www_dir)
        http_server.serve_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
