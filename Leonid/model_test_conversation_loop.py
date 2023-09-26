
from llama_cpp import Llama
import logging

# TEST FILE FOR TEST PURPOSES ONLY

logging.basicConfig(level=logging.INFO)

# Loading the model
logging.info("Loading the model..")
llm = Llama(model_path="./models/ggml-vicuna-13b-4bit-rev1.bin", n_ctx=10000)
logging.info("Model loaded.")

context = "Your name is Leonid"

while True:
    user_input = input()
    if user_input.lower() == 'exit':
        break


    # print(f"context logged: {context}")


    output = llm(f"Context: ({context}). Question: {user_input} Answer:",
                 max_tokens=100,
                 stop=["\n", "Question:", "Q:"],
                 echo=True)

    # Shall we try to append every question and answer to the context each iteration?

    # Consider to drop down 'old' context every X prompts.

    text_line = output['choices'][0]['text']
    # logging.info(f"Context: {text_line}")

    text_line_list = text_line.split("Answer:")
    response_returned = text_line_list[-1]
    print(response_returned)

    adding_to_conversation_context = f" Question: {user_input}, Answer: {response_returned}"
    context = context + adding_to_conversation_context
    # print(context)



