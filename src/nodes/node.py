import atexit
import logging
from abc import abstractmethod, ABC
import asyncio
from traitlets.config.configurable import Configurable

class Node(Configurable):
    logger = logging.getLogger('VEGA')

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.frequency = kwargs.get('frequency', 10)
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

    async def spin(self, frequency: float | None = None):
        self.frequency = frequency or self.frequency or 10
        self._running = True
        self.logger.info(f"*\t{self.__class__.__name__} is spinning at {self.frequency} Hz")

        while self._running:
            self.spinner()
            await asyncio.sleep(1/self.frequency)

    def spin_once(self):
        self.spinner()

    def _shutdown(self):
        self.logger.info(f'{self.__class__.__name__} shutting down')
        self.shutdown()
        
