import logging
from urllib.parse import quote
import feedparser
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class GoogleNewsScraper(BaseScraper):
    """Google News RSS 기반 뉴스 수집"""

    SOURCE_NAME = "구글뉴스"
    RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

    def scrape(self):
        articles = []
        for keyword in self.keywords:
            try:
                items = self._fetch_rss(keyword)
                articles.extend(items)
            except Exception as e:
                logger.error(f"[{self.SOURCE_NAME}] '{keyword}' 검색 실패: {e}")
        # URL 기준 중복 제거
        seen = set()
        unique = []
        for a in articles:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)
        return unique

    def _fetch_rss(self, keyword):
        url = self.RSS_URL.format(query=quote(keyword))
        feed = feedparser.parse(url)
        results = []

        for entry in feed.entries[:30]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            summary = entry.get("summary", "")
            # Google News summary에서 HTML 태그 제거
            if summary:
                from bs4 import BeautifulSoup
                summary = BeautifulSoup(summary, "lxml").get_text(strip=True)

            source_name = ""
            if hasattr(entry, "source"):
                source_name = entry.source.get("title", "")

            results.append({
                "source": f"{self.SOURCE_NAME}({source_name})" if source_name else self.SOURCE_NAME,
                "title": title,
                "url": link,
                "summary": summary[:300],
                "published_date": published,
            })

        logger.info(f"[{self.SOURCE_NAME}] '{keyword}' -> {len(results)}건 수집")
        return results
