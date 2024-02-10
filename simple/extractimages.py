import xml.etree.ElementTree as ET
import random
import json

# Load configuration from a JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

def extract_sitemap_data(xml_file_path, num_urls=200):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    namespaces = {
        'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        'image': 'http://www.google.com/schemas/sitemap-image/1.1'
    }

    all_products = []
    for url in root.findall('ns:url', namespaces):
        loc = url.find('ns:loc', namespaces).text
        image = url.find('image:image', namespaces)
        if image is not None:
            image_loc = image.find('image:loc', namespaces).text
            image_title = image.find('image:title', namespaces).text
            all_products.append((loc, image_loc, image_title))

    # Selecting 200 random products from the list
    if len(all_products) > num_urls:
        return random.sample(all_products, num_urls)
    return all_products

def main():
    xml_file_path = config['sitemap']
    random_entries = extract_sitemap_data(xml_file_path)

    for entry in random_entries:
        print(f"URL: {entry[0]}\nImage URL: {entry[1]}\nTitle: {entry[2]}\n")

if __name__ == "__main__":
    main()