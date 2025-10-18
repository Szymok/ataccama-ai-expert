"""
Enhanced crawler for Ataccama documentation with improved error handling and rate limiting.
"""

import asyncio
import argparse
import os
import re
import time
from urllib.parse import urlparse, urljoin
import logging

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_slug(url: str) -> str:
    """Creates a safe filename from a URL."""
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.strip().lower())
    return slug[:200]

async def crawl_page(page, url, out_dir, allowed_host):
    """Fetches a single page, extracts its content, and saves it."""
    logger.info(f"[FETCHING] -> {url}")
    try:
        # Navigate to the page with timeout
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for the main content area with multiple selectors as fallbacks
        selectors = ["article", "main", "[role='main']", ".content", "#content"]
        content_found = False
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                article_html = await page.inner_html(selector)
                if article_html.strip():
                    content_found = True
                    break
            except:
                continue  # Try next selector
        
        if not content_found:
            logger.warning(f"[WARNING] -> No content found for {url} using known selectors")
            return None, []

        # Convert the HTML of the content area to clean Markdown
        markdown_content = md(article_html, heading_style="ATX")
        
        if not markdown_content.strip():
            logger.warning(f"[WARNING] -> No content found for {url} after conversion to markdown")
            return None, []

        # Save the markdown file
        slug = safe_slug(url)
        md_path = os.path.join(out_dir, f"{slug}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"[SAVED]    -> {md_path}")

        # Find all valid links within the page to crawl next
        links = []
        soup = BeautifulSoup(article_html, 'html.parser')
        
        # Also search in the full page for navigation links
        full_page_html = await page.content()
        full_page_soup = BeautifulSoup(full_page_html, 'html.parser')
        
        # Combine links from content and full page
        all_links = soup.find_all('a', href=True) + full_page_soup.find_all('a', href=True)
        
        for a_tag in all_links:
            href = a_tag.get('href', '')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            
            # Keep only the URL path, ignore fragments and query params for deduplication
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            
            # Only include URLs from allowed host and with .html extension
            if (urlparse(clean_url).netloc == allowed_host and 
                (clean_url.endswith('.html') or '/' in parsed_url.path)):
                # Add the original full URL with params if it was in the content
                full_clean = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}{parsed_url.query}"
                if full_clean.startswith('http'):
                    links.append(full_clean)
        
        # Remove duplicates
        unique_links = list(set(links))
        logger.info(f"[LINKS]   -> Found {len(unique_links)} unique links from {url}")
        
        return url, unique_links

    except Exception as e:
        logger.error(f"[ERROR]    -> Failed to process {url}: {str(e)}")
        return None, []

async def main(start_urls, out_dir, max_pages=100, allowed_host="docs.ataccama.com", delay=1.0):
    """Main function to manage the crawling process with rate limiting."""
    logger.info(f"Starting crawl with max {max_pages} pages")
    
    os.makedirs(out_dir, exist_ok=True)
    
    # Sets for tracking URLs
    urls_to_visit = set(start_urls)
    visited_urls = set()
    failed_urls = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set a reasonable viewport and user agent
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.set_extra_http_headers({"User-Agent": "Ataccama-Docs-Crawler/1.0"})

        while urls_to_visit and len(visited_urls) < max_pages:
            url = urls_to_visit.pop()
            if url in visited_urls or url in failed_urls:
                continue

            visited_urls.add(url)
            
            saved_url, found_links = await crawl_page(page, url, out_dir, allowed_host)
            
            if saved_url:
                for link in found_links:
                    if link not in visited_urls and link not in failed_urls:
                        urls_to_visit.add(link)
            else:
                failed_urls.add(url)

            # Rate limiting - delay between requests
            if delay > 0:
                await asyncio.sleep(delay)

        await browser.close()
        logger.info(f"\nCrawling complete. Saved {len(visited_urls) - len(failed_urls)} pages to '{out_dir}'.")
        if failed_urls:
            logger.info(f"Failed to crawl {len(failed_urls)} pages.")

def parse_args():
    ap = argparse.ArgumentParser(
        description='Crawl Ataccama documentation with improved error handling and rate limiting'
    )
    ap.add_argument("--start", nargs="+", required=True, help="Seed URLs to start crawling from")
    ap.add_argument("--out", required=True, help="Output directory for Markdown files")
    ap.add_argument("--max-pages", type=int, default=100, help="Maximum pages to crawl (default: 100)")
    ap.add_argument("--domain", default="docs.ataccama.com", help="Domain to restrict crawling to (default: docs.ataccama.com)")
    ap.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds (default: 1.0)")
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.start, args.out, args.max_pages, args.domain, args.delay))