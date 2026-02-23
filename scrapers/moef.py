import logging
import feedparser
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class MoefScraper(BaseScraper):
    """기획재정부 보도자료 RSS 스크래퍼"""

    SOURCE_NAME = "기획재정부"
    RSS_URL = "https://www.moef.go.kr/com/detailRssTagService.do?bbsId=MOSFBBS_000000000028"

    def scrape(self):
        articles = []
        try:
            feed = feedparser.parse(self.RSS_URL)
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
            logger.info(f"[{self.SOURCE_NAME}] RSS -> {len(articles)}건 수집")
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] RSS 수집 실패: {e}")
        return articles
