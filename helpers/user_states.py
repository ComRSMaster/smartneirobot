from telebot.asyncio_filters import AdvancedCustomFilter


class States:
    AI_TALK = 1


class UserStateFilter(AdvancedCustomFilter):
    key = 'state'

    async def check(self, msg, state):
        if state == '*':
            return msg.state != -1
        return state == msg.state
