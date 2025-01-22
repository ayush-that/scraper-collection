import requests
import json
import time
import random

API_KEY = "AIzaSyDAnLROobruaMjKQH4bUNzaO5YMyuMxvak"
SEARCH_ENGINE_ID = "d16b6455dd9e240c6"
num_results = 1

with open("banks.json", "r") as banks_file:
    banks = json.load(banks_file)

with open("links.txt", "w") as file:
    for bank_name, website in banks.items():
        query = f"{bank_name} site:{website} basel III -filetype:pdf"
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={SEARCH_ENGINE_ID}&num={num_results}"

        response = requests.get(url)
        if response.status_code == 200:
            results = response.json()
            for item in results.get("items", []):
                file.write(f"{item['link']}\n")

        time.sleep(random.uniform(1, 3))
