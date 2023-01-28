import os
import openai
import logging

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
                activation_check = self.send_input("Are you alive?")

                if isinstance(activation_check, str) and len(activation_check) > 0:
                    return True

                return False

            else:
                return False

        except Exception as e:
            logging.warning(f"Can't establish communication with ChatGPT: {e}")
            return False

    def send_input(self, verbal_input, model="text-babbage-001", temperature=0.7, max_tokens=256):

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

        return extracted_data


if __name__ == "__main__":
    chtgpt = ChatGPTIntegration()
    #print(chtgpt.is_chatgpt_available())
    # reaction = chtgpt.send_input("Are you alive?")
    # print(reaction)
    # print(type(reaction))
    # print(len(reaction))