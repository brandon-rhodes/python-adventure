import abc
import io
from typing import NamedTuple, Optional


class SavesGateway(abc.ABC):
    @abc.abstractmethod
    def fetch_save(self, sms_number: str) -> Optional[io.BytesIO]:
        ...

    @abc.abstractmethod
    def update_save(self, sms_number: str, save: io.BytesIO) -> None:
        ...


class GameGateway(abc.ABC):
    @abc.abstractmethod
    def resume(self, save: io.BytesIO) -> None:
        ...

    @abc.abstractmethod
    def start(self) -> str:
        ...

    @abc.abstractmethod
    def do_command(self, command: str) -> str:
        ...

    @abc.abstractmethod
    def save(self) -> io.BytesIO:
        ...


class Context(NamedTuple):
    game: GameGateway
    saves: SavesGateway
