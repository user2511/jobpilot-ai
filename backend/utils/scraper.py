# backend/utils/scraper.py
# Scrapes job description text from a URL using BeautifulSoup.
# Simple and focused — no browser automation, no Selenium.

import requests
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Selectors to try in order — covers most job boards
JD_SELECTORS = [
    {"class": "job-description"},
    {"class": "jobDescriptionContent"},
    {"class": "description__text"},          # LinkedIn
    {"id": "jobDescriptionText"},            # Indeed
    {"class": "job-details-jobs-unified-top-card__job-description"},
    {"class": "jobsearch-jobDescriptionText"},
    {"data-automation": "jobAdDetails"},     # Seek
    {"class": "posting-description"},
]


def scrape_jd_from_url(url: str) -> str:
    """
    Fetch and extract job description text from a URL.

    Tries known CSS selectors for major job boards first,
    falls back to extracting all paragraph text from the page.

    Args:
        url: Job posting URL

    Returns:
        Extracted job description text

    Raises:
        ValueError: If page cannot be fetched or no content found
    """
    try:
        logger.info(f"Scraping JD from: {url}")
        session = requests.Session()

        response = session.get(url,headers={**HEADERS,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
    },timeout=15,
)       
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Response text preview: {response.text[:500]}")

 
     

        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script, style, nav, footer noise
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Try known JD selectors first
        for selector in JD_SELECTORS:
            element = soup.find(attrs=selector)
            if element:
                text = element.get_text(separator="\n", strip=True)
                if len(text) > 200:    # sanity check — real JD should be longer
                    logger.info(f"JD scraped via selector {selector}: {len(text)} chars")
                    return text

        # Fallback: grab all paragraph text
       
        main_text = soup.get_text(separator="\n", strip=True)

        # Remove excessive blank lines
        lines = [line.strip() for line in main_text.splitlines()]
        lines = [line for line in lines if len(line) > 2]

        text = "\n".join(lines)


       # text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        if len(text) < 500:
            raise ValueError("Could not extract meaningful content from URL. Try pasting the JD text directly.")

        logger.info(f"JD scraped via fallback paragraphs: {len(text)} chars")
        return text

    except requests.exceptions.Timeout:
        raise ValueError(f"Request timed out fetching URL: {url}")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error fetching URL: {e}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch URL: {e}")
