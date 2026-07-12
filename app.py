from ollama import Client

MODEL="qwen2.5vl:7b"
client=Client(host="http://localhost:11434")

prompt="Hey there are you present?"
res=client.generate(model=MODEL, prompt=prompt)
print(res["response"])