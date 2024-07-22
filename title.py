import requests
from bs4 import BeautifulSoup
import concurrent.futures

def get_title(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "No title found"
        return url, title.strip()
    except Exception as e:
        return url, f"Error: {str(e)}"

def get_titles(urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_title, urls))
    return results

if __name__=='__main__':
    # Example usage
    urls = [
        "https://www.example.com",
        "https://www.python.org",
        "https://www.github.com"
    ]

    results = get_titles(urls)

    for url, title in results:
        print(f"URL: {url}")
        print(f"Title: {title}")
        print("-" * 50)