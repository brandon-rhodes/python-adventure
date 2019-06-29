import io
import re
from typing import Optional

import adventure
from adventure.game import Game

from sms_adventure.definitions import GameGateway as GameGatewayABC


class GameGateway(GameGatewayABC):
    game: Optional[Game]

    def __init__(self) -> None:
        self.game = None

    def start(self) -> str:
        if self.game:
            raise GameAlreadyStartedError

        self.game = Game()
        adventure.load_advent_dat(self.game)
        self.game.start()
        return self.game.output

    def resume(self, save: io.BytesIO) -> None:
        if self.game:
            raise GameAlreadyStartedError

        self.game = Game.resume(save)

    def do_command(self, command: str) -> str:
        if not self.game:
            raise GameNotStartedError

        words = re.findall(r"\w+", command)
        return self.game.do_command(words)

    def save(self) -> io.BytesIO:
        if not self.game:
            raise GameNotStartedError

        save_data_stream = io.BytesIO()
        self.game.t_suspend(verb=None, obj=save_data_stream)
        return save_data_stream


class GameNotStartedError(Exception):
    message = "Game has not been started"


class GameAlreadyStartedError(Exception):
    message = "Game already started"
