from sms_adventure.definitions import Context


def do_sms_command(context: Context, command_text: str, from_sms_number: str) -> str:
    last_save = context.saves.fetch_save(from_sms_number)
    if last_save:
        context.game.resume(last_save)
    else:
        context.game.start()

    response_text = context.game.do_command(command_text)
    new_save = context.game.save()

    context.saves.update_save(from_sms_number, new_save)

    return response_text
