"""
Run the full raw data ingestion pipeline:
1) Crawl HTML pages
2) Collect linked/downloadable PDFs
3) Build a manifest of all raw files

This uses the html_crawler, pdf_collector, and raw_cataloger modules.
"""

from src.scraping import html_crawler, pdf_collector, raw_cataloger

def main():
    print("=== STEP 1: Crawl HTML pages ===")
    html_crawler.main()

    print("\n=== STEP 2: Collect PDFs ===")
    pdf_collector.main()

    print("\n=== STEP 3: Build raw manifest ===")
    raw_cataloger.main()

    print("\nPipeline complete!")

if __name__ == "__main__":
    main()
