import json

with open("pdf_links.json", "r") as file:
    links = json.load(file)

unique_links = list(set(links))

with open("pdf_links.json", "w") as file:
    json.dump(unique_links, file, indent=4)
