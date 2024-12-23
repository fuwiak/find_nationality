import requests
from bs4 import BeautifulSoup
import time

# Base URLs for boy and girl names
base_urls = {
    "boy": "https://islam-mama.com/names/boy",
    "girl": "https://islam-mama.com/names/girl"
}

# Dictionary to store the extracted names for both categories
names = {
    "boy": [],
    "girl": []
}

# Loop through both boy and girl base URLs
for gender, base_url in base_urls.items():
    page = 1
    while True:
        # Construct the URL with the current page number
        url = f"{base_url}?page={page}"

        # Fetch the page content
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code != 200:
            print(f"Failed to retrieve page {page} for {gender}.")
            break

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all list items with class 'names-list-item'
        list_items = soup.find_all('li', class_='names-list-item')

        # If no names are found, we've reached the last page
        if not list_items:
            print(f"No more names found for {gender}. Exiting.")
            break

        # Extract names from the current page
        for item in list_items:
            main_tag = item.find('main')
            if main_tag:
                name_tag = main_tag.find('a', title=True)
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    names[gender].append(name)

        print(f"Page {page} for {gender} processed.")

        # Increment the page counter to move to the next page
        page += 1

        # Optional: Pause between requests to be respectful to the server
        time.sleep(1)

# Save the names to a single text file
with open("islam_names.txt", "w", encoding="utf-8") as file:
    for gender in names:
        # Add a section header for each gender
        file.write(f"--- {gender.capitalize()} Names ---\n")
        for name in names[gender]:
            file.write(f"{name}\n")  # Write each name on a new line
        file.write("\n")  # Add an empty line between sections

print("Names saved to islam_names.txt.")
