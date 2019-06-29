import sys

from sms_adventure.file_system_saves import FileSystemSavesGateway
from sms_adventure.definitions import Context
from sms_adventure.game import GameGateway
from sms_adventure.use_adventure import do_sms_command
from sms_adventure.exceptions import CommandPolicyViolationError

game = GameGateway()
file_system_saves = FileSystemSavesGateway()
context = Context(game=game, saves=file_system_saves)

sms_number = sys.argv[1]
command = sys.argv[2]

try:
    output = do_sms_command(context, command, sms_number)
except CommandPolicyViolationError as e:
    print(f"*COMMAND POLICY VIOLATION ERROR: {str(e)}*")
else:
    print(output)
