import requests

API_KEY = "AIzaSyDAnLROobruaMjKQH4bUNzaO5YMyuMxvak"
SEARCH_ENGINE_ID = "d16b6455dd9e240c6"
num_results = 1

query = "idbi bank basel iii -filetype:pdf"
url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={SEARCH_ENGINE_ID}&num={num_results}"

response = requests.get(url)

with open("links.txt", "w") as file:
    if response.status_code == 200:
        results = response.json()
        for item in results.get("items", []):
            file.write(f"{item['link']}\n")
