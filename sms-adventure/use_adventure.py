def do_sms_command(context: Context, command_text: str, from_sms_number: str) -> str:
    last_save = context.saves_gateway.fetch_save(from_sms_number)
    if last_save:
        context.game_gateway.resume(last_save)
    else:
        context.game_gateway.start()

    response_text = context.game_gateway.do_command(command_text)
    new_save = context.game_gateway.save()

    context.saves_gateway.update_save(from_sms_number, new_save)

    return response_text
