import requests
from bs4 import BeautifulSoup
import time
import re
hebrew_letters = [
    'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'כ', 'ך',
    'ל', 'מ', 'ם', 'נ', 'ן', 'ס', 'ע', 'פ', 'ף', 'צ', 'ץ', 'ק',
    'ר', 'ש', 'ת'
]
def scrape_pealim(total_pages=618):
    all_words = []
    base_url = "https://www.pealim.com/he/dict/?page="

    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for page_num in range(1, total_pages + 1):
        print(f"Scraping page {page_num}...")
        url = f"{base_url}{page_num}"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Check for HTTP errors

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the dictionary table
            table = soup.find('table')
            if table:
                # Find all rows in the table body
                rows = table.find_all('tr')[1:]  # Skip the header row
                for row in rows:
                    cols = row.find_all('td')
                    if cols:
                        # Assuming 'מילה' is the first or second column
                        # You can adjust the index [0] based on the site's layout
                        word = only_heberw(cols[0].get_text(strip=True))
                        if 5 <= word <= 8:
                            all_words.append(word)

            # Be polite to the server
            time.sleep(0.01)

        except Exception as e:
            print(f"Error on page {page_num}: {e}")
            break

    return all_words
def clean_hebrew(text):
    # This regex keeps only standard Hebrew letters and removes vowels/points
    return re.sub(r'[^\u05D0-\u05EA]', '', text)
def only_heberw(word):
    new_word = ""
    for l in word:
        if l in hebrew_letters:
            new_word += clean_hebrew(l)
    return new_word
def main():
    with open(r"C:\Users\User\Downloads\words.txt","w") as f:
        f.write(";".join(scrape_pealim()))

main()