# Import Built-Ins
import logging
import time
from threading import Thread
from collections import defaultdict
from queue import Queue
# Import Third-Party

# Import Homebrew

# Init Logging Facilities
log = logging.getLogger(__name__)


from websocket import create_connection, WebSocketTimeoutException


class GeminiWss:
    def __init__(self, endpoints=None):

        self.endpoints = endpoints if endpoints else []
        self.endpoint_threads = {}
        self.running = defaultdict(bool)
        self.endpoint_qs = defaultdict(Queue)

        self.addr = 'wss://api.gemini.com/v1/'

    def start(self):
        self.running = True
        for endpoint in self.endpoints:
            self.running[endpoint] = True
            t = Thread(target=self._subscription_thread,
                       args=(endpoint,))
            t.daemon = True
            t.start()
            self.endpoint_threads[endpoint] = t

    def stop(self):
        for endpoint in self.endpoints:
            self.running[endpoint] = False
            self.endpoint_threads[endpoint].join()
            while not self.endpoint_qs[endpoint].empty:
                time.sleep(.5)
            self.endpoint_qs.pop(endpoint)

        self.garbage_collector()

    def restart(self):
        self.stop()
        self.start()

    def subscribe(self, endpoint):
        return create_connection(self.addr + endpoint, timeout=1)

    def garbage_collector(self):
        for endpoint in self.endpoints:
            # check all caches for dead threads and clean up
            if self.endpoint_threads[endpoint].isalive():
                continue
            else:
                self.endpoint_threads.pop(endpoint)
                while not self.endpoint_qs[endpoint].empty():
                    time.sleep(0.5)

                if endpoint in self.endpoint_qs:
                    self.endpoint_qs.pop(endpoint)

                try:
                    self.running.pop(endpoint)
                except KeyError:
                    pass

    def unsubscribe(self, endpoint):
        self.running[endpoint] = False
        self.endpoint_threads[endpoint].join()
        while not self.endpoint_qs[endpoint].empty():
            time.sleep(1)

        self.endpoint_threads.pop(endpoint)
        self.running.pop(endpoint)
        self.endpoint_qs.pop(endpoint)

    def _subscription_thread(self, endpoint):
        conn = self.subscribe(endpoint)

        while self.running[endpoint]:
            try:
                msg = conn.recv()
            except WebSocketTimeoutException:
                raise

            self.endpoint_qs[endpoint].put(msg)





