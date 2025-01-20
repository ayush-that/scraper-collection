import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def download_pdfs_concurrently(links, directory, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_pdf, link, directory): link for link in links
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error downloading {url}: {e}")


download_pdfs_concurrently(pdf_links, "downloaded_pdfs", max_workers=10)
