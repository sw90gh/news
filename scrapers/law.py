import logging
from urllib.parse import quote
import feedparser
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LawScraper(BaseScraper):
    """법령/입법 동향 - Google News RSS 기반 수집"""

    SOURCE_NAME = "국가법령정보센터"
    RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

    # 법령 관련 전용 검색어
    LAW_KEYWORDS = [
        "공공기관 정원 법령 개정",
        "정부조직법 개정",
        "총정원령 개정",
        "행정기관 정원 시행령",
    ]

    def scrape(self):
        articles = []
        for keyword in self.LAW_KEYWORDS:
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

        for entry in feed.entries[:15]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            summary = entry.get("summary", "")
            if summary:
                from bs4 import BeautifulSoup
                summary = BeautifulSoup(summary, "lxml").get_text(strip=True)

            results.append({
                "source": self.SOURCE_NAME,
                "title": title,
                "url": link,
                "summary": summary[:300],
                "published_date": published,
            })

        logger.info(f"[{self.SOURCE_NAME}] '{keyword}' -> {len(results)}건 수집")
        return results
