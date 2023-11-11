import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'WSearch Spyder'
}
strip_symbol_list = [",",".","(",")","\"","'",";",":","!","[","]","-","–","—","/","{","}","^","%","$","£","¢","¥","€","#","@"]

def download(url):
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print("Error: "+str(response.status_code))

def strip_symbols(text):
    translation_table = str.maketrans({key: ' ' for key in strip_symbol_list})
    return text.translate(translation_table)

def extract_text(html):
    soup = BeautifulSoup(html, 'lxml')

    # Extracting text from the title tag
    title_text = soup.title.string if soup.title else ''

    # Extracting visible text
    visible_text = ' '.join(soup.stripped_strings)

    # Extracting alt text from images
    alt_text = ' '.join(img['alt'] for img in soup.find_all('img', alt=True))

    # Combine all extracted text
    all_text = ' '.join(filter(None, [title_text, visible_text, alt_text]))

    return all_text

result = extract_text(download("https://en.wikipedia.org/wiki/Semantic_satiation"))
print(result)
print(strip_symbols(result))
