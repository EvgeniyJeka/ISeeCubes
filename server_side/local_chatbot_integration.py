
class LocalChatBotIntegration:

    def check_if_bot_available(self, bot_name: str):
        # Temporary stab. The method will send a request to verify that bot with given name/ID is available

        return True


    def route_incoming_message(self, bot_name, user_name, message_content):
        if bot_name == 'Leonid':
            return self.send_message_to_leonid(user_name, message_content)


    def send_message_to_leonid(self, user_name, message_content):
        content = "Hello there! I'm leonid."
        return content