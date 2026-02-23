import logging
from urllib.parse import quote
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class NaverNewsScraper(BaseScraper):
    """네이버 뉴스 검색 스크래퍼"""

    SOURCE_NAME = "네이버뉴스"

    def scrape(self):
        articles = []
        for keyword in self.keywords:
            try:
                items = self._search_keyword(keyword)
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

    def _search_keyword(self, keyword):
        encoded = quote(keyword)
        url = f"https://search.naver.com/search.naver?where=news&query={encoded}&sort=1&ds=&de=&nso=so:dd,p:1y"
        resp = self.fetch(url)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        news_items = soup.select("div.news_area")
        for item in news_items[:20]:
            try:
                title_tag = item.select_one("a.news_tit")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                link = title_tag.get("href", "")

                summary_tag = item.select_one("div.news_dsc")
                summary = summary_tag.get_text(strip=True) if summary_tag else ""

                info_tag = item.select_one("span.info")
                date = info_tag.get_text(strip=True) if info_tag else ""

                results.append({
                    "source": self.SOURCE_NAME,
                    "title": title,
                    "url": link,
                    "summary": summary[:300],
                    "published_date": date,
                })
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] 항목 파싱 오류: {e}")
                continue

        logger.info(f"[{self.SOURCE_NAME}] '{keyword}' -> {len(results)}건 수집")
        return results
