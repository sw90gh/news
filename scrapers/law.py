import logging
from urllib.parse import quote
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LawScraper(BaseScraper):
    """국가법령정보센터 법령 검색 스크래퍼"""

    SOURCE_NAME = "국가법령정보센터"
    SEARCH_URL = "https://www.law.go.kr/LSW/lsSc.do"

    def scrape(self):
        articles = []
        search_terms = ["공공기관 정원", "정부조직법", "총정원령", "행정기관 정원"]
        for term in search_terms:
            try:
                items = self._search(term)
                articles.extend(items)
            except Exception as e:
                logger.error(f"[{self.SOURCE_NAME}] '{term}' 검색 실패: {e}")
        # URL 기준 중복 제거
        seen = set()
        unique = []
        for a in articles:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)
        return unique

    def _search(self, term):
        params = {
            "menuId": "7",
            "subMenuId": "41",
            "tabMenuId": "141",
            "query": term,
            "section": "lmSc",
        }
        resp = self.fetch(self.SEARCH_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        rows = soup.select("div.srchRst li, table.srch_list tbody tr, div.list_item")
        for row in rows[:15]:
            try:
                link_tag = row.select_one("a")
                if not link_tag:
                    continue
                title = link_tag.get_text(strip=True)

                href = link_tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://www.law.go.kr" + href

                date_tag = row.select_one("span.date, td.date, span.txt_date")
                date = date_tag.get_text(strip=True) if date_tag else ""

                results.append({
                    "source": self.SOURCE_NAME,
                    "title": title,
                    "url": href,
                    "summary": f"검색어: {term}",
                    "published_date": date,
                })
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] 항목 파싱 오류: {e}")
                continue

        logger.info(f"[{self.SOURCE_NAME}] '{term}' -> {len(results)}건 수집")
        return results
