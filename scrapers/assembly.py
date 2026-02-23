import logging
from urllib.parse import quote
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AssemblyScraper(BaseScraper):
    """열린국회정보 - 의안 검색 스크래퍼"""

    SOURCE_NAME = "열린국회정보"
    SEARCH_URL = "https://likms.assembly.go.kr/bill/BillSearchResult.do"

    def scrape(self):
        articles = []
        search_terms = ["공공기관 정원", "정부조직법", "총정원"]
        for term in search_terms:
            try:
                items = self._search(term)
                articles.extend(items)
            except Exception as e:
                logger.error(f"[{self.SOURCE_NAME}] '{term}' 검색 실패: {e}")
        seen = set()
        unique = []
        for a in articles:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)
        return unique

    def _search(self, term):
        params = {
            "billName": term,
            "pageSize": "20",
        }
        resp = self.fetch(self.SEARCH_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        rows = soup.select("table tbody tr, div.srch_list li")
        for row in rows[:15]:
            try:
                link_tag = row.select_one("a")
                if not link_tag:
                    continue
                title = link_tag.get_text(strip=True)
                if not title:
                    continue

                href = link_tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://likms.assembly.go.kr" + href

                # 날짜 정보 추출
                tds = row.select("td")
                date = ""
                for td in tds:
                    text = td.get_text(strip=True)
                    if len(text) == 10 and text.count("-") == 2:
                        date = text
                        break
                    if len(text) == 10 and text.count(".") == 2:
                        date = text
                        break

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
