# crawl_ataccama_docs.py
# Usage:
#   pip install playwright beautifulsoup4 markdownify
#   python -m playwright install --with-deps chromium
#   python crawl_ataccama_docs.py --start https://docs.ataccama.com/one/latest/overview.html --out ./ataccama_docs_output

import asyncio
import argparse
import os
import re
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from markdownify import markdownify as md

ALLOWED_HOST = "docs.ataccama.com"

def safe_slug(url: str) -> str:
    """Creates a safe filename from a URL."""
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.strip().lower())
    return slug[:200]

async def crawl_page(page, url, out_dir):
    """Fetches a single page, extracts its content, and saves it."""
    print(f"[FETCHING] -> {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # This is the key: wait for the <article> element to be loaded by JavaScript
        await page.wait_for_selector("article", timeout=30000)
        
        # Extract the HTML from the main content area
        article_html = await page.inner_html('article')
        
        # Convert the HTML of the article to clean Markdown
        markdown_content = md(article_html, heading_style="ATX")
        
        if not markdown_content.strip():
            print(f"[WARNING]  -> No content found for {url}")
            return None, []

        # Save the markdown file
        slug = safe_slug(url)
        md_path = os.path.join(out_dir, f"{slug}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"[SAVED]    -> {md_path}")

        # Find all valid links within the article to crawl next
        links = []
        soup = BeautifulSoup(article_html, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            # Keep only the URL path, ignore fragments
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            if urlparse(clean_url).netloc == ALLOWED_HOST:
                links.append(clean_url)
        
        return url, links

    except Exception as e:
        print(f"[ERROR]    -> Failed to process {url}: {e}")
        return None, []

async def main(start_urls, out_dir, max_pages, max_depth):
    """Main function to manage the crawling process."""
    os.makedirs(out_dir, exist_ok=True)
    
    # Sets for tracking URLs
    urls_to_visit = set(start_urls)
    visited_urls = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        while urls_to_visit and len(visited_urls) < max_pages:
            url = urls_to_visit.pop()
            if url in visited_urls:
                continue

            visited_urls.add(url)
            
            saved_url, found_links = await crawl_page(page, url, out_dir)
            
            if saved_url:
                for link in found_links:
                    if link not in visited_urls:
                        urls_to_visit.add(link)

        await browser.close()
        print(f"\nCrawling complete. Saved {len(visited_urls)} pages to '{out_dir}'.")

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", nargs="+", required=True, help="Seed URLs under https://docs.ataccama.com")
    ap.add_argument("--out", required=True, help="Output directory for Markdown")
    ap.add_argument("--max-pages", type=int, default=100, help="Maximum pages to crawl")
    # Note: max-depth is not implemented in this simpler script to keep it clean.
    # It primarily follows links found on the pages up to max_pages.
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # This simple script doesn't use max_depth, but you can add it if needed
    asyncio.run(main(args.start, args.out, args.max_pages, max_depth=0))