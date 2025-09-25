from llm import LLAMA

def chat(system_message, user_message):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    return LLAMA.invoke(messages).content


# usage
response = chat("You are a helpful assistant.", "Hello, world!")
print(response)