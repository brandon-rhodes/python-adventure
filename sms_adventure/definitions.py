import abc
from typing import NamedTuple


class SavesGateway(abc.ABC):
    @abc.abstractmethod
    def fetch_save(self, sms_number: str) -> bytes:
        ...

    @abc.abstractmethod
    def update_save(self, sms_number: str, save: bytes) -> None:
        ...


class GameGateway(abc.ABC):
    @abc.abstractmethod
    def resume(self, save: bytes) -> None:
        ...

    @abc.abstractmethod
    def start(self) -> None:
        ...

    @abc.abstractmethod
    def do_command(self, command: str) -> str:
        ...

    @abc.abstractmethod
    def save(self) -> str:
        ...


class Context(NamedTuple):
    game: GameGateway
    saves: SavesGateway
