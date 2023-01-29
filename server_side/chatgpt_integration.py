import os
import openai
import logging

USE_TOKENS_TO_TEST_CONNECTION = False

CHAT_GPT_SELECTED_MODEL = 'text-davinci-002'
#CHAT_GPT_SELECTED_MODEL = 'text-babbage-001'

class ChatGPTIntegration:

    def is_chatgpt_available(self):
        """
        This method can be used to validate, that a communication with ChatGPT can be established.
        Returns True on success.

        :return: bool
        """
        try:
            key = os.getenv("OPENAI_API_KEY")

            if key and len(key) > 0:
                if USE_TOKENS_TO_TEST_CONNECTION:

                    activation_check = self.send_input("Are you alive?")
                    logging.info(f"ChatGPT Integration: ChatGPT replied to the activation check: {activation_check}")

                    if isinstance(activation_check, str) and len(activation_check) > 0:
                        return True
                    else:
                        return False

                else:
                    return True

            else:
                return False

        except Exception as e:
            logging.warning(f"ChatGPT Integration: Can't establish communication with ChatGPT: {e}")
            return False

    def send_input(self, verbal_input, model=CHAT_GPT_SELECTED_MODEL, temperature=0.4, max_tokens=256):

        response = openai.Completion.create(
            model=model,
            prompt=verbal_input,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        extracted_data = response["choices"][0]["text"]
        cleared_data = extracted_data.replace("\n", "")

        return cleared_data


if __name__ == "__main__":
    chtgpt = ChatGPTIntegration()
    #print(chtgpt.is_chatgpt_available())
    # reaction = chtgpt.send_input("Are you alive?")
    # print(reaction)
    # print(type(reaction))
    # print(len(reaction))
