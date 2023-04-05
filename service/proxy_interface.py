import abc


class ProxyInterface(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'filter_trafic') and
                callable(subclass.filter_trafic) or
                NotImplemented)

    @abc.abstractmethod
    def filter_trafic(self):
        """ 
            filter trafic of a device (computer,phone)
        """
        pass

    @abc.abstractmethod
    def get_open_port(host: str) -> list:
        """ 
            get different port open on a device
        """
        pass
