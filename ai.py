import requests

API_KEY = "sk-ef686fe5ad12475783edc35c67a90a0b"
BASE_URL = "https://api.deepseek.com"

with open("result.txt", "r", encoding="utf-8") as file:
    content = file.read()

prompt = "I am providing you with a Crawl4AI markdown result. Your job is to get/contruct all possible links to download PDFs. Give me the links in JSON format"

response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    },
    json={
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt + "\n" + content}],
    },
)

response_json = response.json()
response_text = response_json["choices"][0]["message"]["content"]

with open("response.txt", "w") as file:
    file.write(response_text)

print("Response text saved to response.txt")