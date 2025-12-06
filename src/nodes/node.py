import atexit
import logging
import threading
import time
from abc import abstractmethod

import traitlets
from traitlets.config.configurable import Configurable


class Node(Configurable):
    logger = logging.getLogger('VEGA')
    frequency = traitlets.Float(default_value=10).tag(config=True)

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        print("\n")
        self.logger.info("*" * 50 + "\n")
        self.logger.info(f"*\tStarting {self.__class__.__name__} Node @ {self.frequency}Hz\n")
        self.logger.info("*" * 50 + "\n")
        self._thread = None
        self._running = False
        atexit.register(self._shutdown)

    def loaded(self):
        print("\n")
        self.logger.info("*" * 50 + "\n")
        self.logger.info(f"*\t{self.__class__.__name__} Node is up\n")
        self.logger.info("*" * 50 + "\n")

    @abstractmethod
    def spinner(self):
        pass

    def shutdown(self):
        pass

    def _spin(self):
        while self._running:
            self.spinner()
            time.sleep(1.0 / self.frequency)

    def spin(self, frequency: int = 10):
        self.logger.info(f'Spinning {self.__class__.__name__} at {frequency}Hz')
        self.frequency = frequency
        self._running = True
        self._thread = threading.Thread(target=self._spin)
        self._thread.daemon = True
        self._thread.start()

    def spin_once(self):
        self.spinner()

    def _shutdown(self):
        self.shutdown()
        self._running = False
        if self._thread:
            self.logger.info(f'{self.__class__.__name__} shutting down')
        try:
            self._thread.join()
        except Exception as ex:
            self.logger.error(f'{ex.__str__()}')
