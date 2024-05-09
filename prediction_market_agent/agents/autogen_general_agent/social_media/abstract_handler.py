import typing as t
from abc import ABCMeta, abstractmethod


class AbstractSocialMediaHandler(metaclass=ABCMeta):
    client: t.Any

    @abstractmethod
    def post(self, text: str) -> None:
        pass
