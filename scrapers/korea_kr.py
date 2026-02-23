import logging
import feedparser
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class KoreaKrScraper(BaseScraper):
    """정책브리핑(korea.kr) RSS 스크래퍼"""

    SOURCE_NAME = "정책브리핑"
    RSS_URLS = [
        "https://www.korea.kr/rss/pressrelease.xml",
        "https://www.korea.kr/rss/ebriefing.xml",
    ]

    def scrape(self):
        articles = []
        for rss_url in self.RSS_URLS:
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries:
                    title = entry.get("title", "")
                    if not self.matches_keyword(title):
                        continue
                    link = entry.get("link", "")
                    published = entry.get("published", "")
                    summary = entry.get("summary", entry.get("description", ""))

                    articles.append({
                        "source": self.SOURCE_NAME,
                        "title": title,
                        "url": link,
                        "summary": summary[:300] if summary else "",
                        "published_date": published,
                    })
                logger.info(f"[{self.SOURCE_NAME}] {rss_url} -> 필터 후 {len(articles)}건")
            except Exception as e:
                logger.error(f"[{self.SOURCE_NAME}] RSS 수집 실패 ({rss_url}): {e}")
        return articles
