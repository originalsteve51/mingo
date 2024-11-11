# mingo_web_monitor.py

import threading
import time
import requests

# Global integer variable
counter = 0

class WebMonitor:
    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run)
            self._thread.start()
    
    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join()
    
    def _run(self):
        global counter
        while self._running:
            stop_count = int(requests.get('http://localhost:8080/get_stop_count').content)
            print(counter, stop_count)
            counter += 1
            time.sleep(1)

def test():
    monitor = WebMonitor()
    monitor.start()
    
    # Let the thread run for a while (e.g., 10 seconds)
    time.sleep(100)
    
    # Stop the thread
    monitor.stop()
    print("Counter incrementing stopped.")

def get(url, params=None, **kwargs):
    r"""Sends a GET request.
    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary, list of tuples or bytes to send
        in the query string for the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    kwargs.setdefault('allow_redirects', True)
    return request('get', url, params=params, **kwargs)    

if __name__ == "__main__":
    test()