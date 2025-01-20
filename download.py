import os
import requests
import json

with open("pdf_links.json", "r") as file:
    pdf_links = json.load(file)

os.makedirs("downloaded_pdfs", exist_ok=True)


def download_pdf(url, directory):
    try:
        response = requests.get(url)
        response.raise_for_status()
        filename = os.path.join(directory, url.split("/")[-1])
        with open(filename, "wb") as pdf_file:
            pdf_file.write(response.content)
        print(f"Downloaded: {filename}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")


for link in pdf_links:
    download_pdf(link, "downloaded_pdfs")
