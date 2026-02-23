import logging
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class MoisScraper(BaseScraper):
    """행정안전부 보도자료 스크래퍼"""

    SOURCE_NAME = "행정안전부"
    LIST_URL = "https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardList.do"

    def scrape(self):
        articles = []
        try:
            for page in range(1, 4):
                items = self._fetch_page(page)
                articles.extend(items)
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] 스크래핑 실패: {e}")
        return articles

    def _fetch_page(self, page):
        params = {
            "bbsId": "BBSMSTR_000000000012",
            "pageIndex": page,
        }
        resp = self.fetch(self.LIST_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        rows = soup.select("table.board_list tbody tr, ul.board_list li, div.brd_list li")
        for row in rows:
            try:
                link_tag = row.select_one("a")
                if not link_tag:
                    continue
                title = link_tag.get_text(strip=True)
                if not self.matches_keyword(title):
                    continue

                href = link_tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://www.mois.go.kr" + href

                date_tag = row.select_one("td.date, span.date, td:nth-of-type(4)")
                date = date_tag.get_text(strip=True) if date_tag else ""

                results.append({
                    "source": self.SOURCE_NAME,
                    "title": title,
                    "url": href,
                    "summary": "",
                    "published_date": date,
                })
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] 항목 파싱 오류: {e}")
                continue

        logger.info(f"[{self.SOURCE_NAME}] 페이지 {page} -> {len(results)}건 수집")
        return results
