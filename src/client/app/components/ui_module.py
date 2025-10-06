from abc import ABC, abstractmethod


class UIModule(ABC):
    @abstractmethod
    def show(self, **kargs):
        pass