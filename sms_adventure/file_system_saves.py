import io
import os
from pathlib import Path
from typing import Optional

from sms_adventure.definitions import SavesGateway


class FileSystemSavesGateway(SavesGateway):
    saves_directory_path: Path

    def __init__(self, saves_directory: Optional[str] = None) -> None:
        self.saves_directory_path = Path(saves_directory or "sms_adventure_file_saves")
        if not self.saves_directory_path.exists():
            os.makedirs(self.saves_directory_path)

    def fetch_save(self, sms_number: str) -> Optional[io.BytesIO]:
        save_file_path = self.saves_directory_path / sms_number
        if not save_file_path.exists():
            return None

        with open(save_file_path, "rb") as save_file:
            return io.BytesIO(save_file.read())

    def update_save(self, sms_number: str, save: io.BytesIO) -> None:
        save_file_path = self.saves_directory_path / sms_number
        with open(save_file_path, "wb") as save_file:
            save_file.write(save.getvalue())
