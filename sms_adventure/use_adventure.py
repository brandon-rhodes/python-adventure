from sms_adventure.definitions import Context
from sms_adventure.exceptions import CommandPolicyViolationError
from sms_adventure import policies


def do_sms_command(context: Context, command_text: str, from_sms_number: str) -> str:
    command_invalid_reason = policies.command.invalid_reason(command_text)
    if command_invalid_reason:
        raise CommandPolicyViolationError(command_invalid_reason)

    last_save = context.saves.fetch_save(from_sms_number)
    if last_save:
        context.game.resume(last_save)
        response_text = context.game.do_command(command_text)
    else:
        response_text = context.game.start()

    new_save = context.game.save()
    context.saves.update_save(from_sms_number, new_save)

    return response_text
