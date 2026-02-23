import logging
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class MpmScraper(BaseScraper):
    """인사혁신처 보도자료 스크래퍼"""

    SOURCE_NAME = "인사혁신처"
    BASE_URL = "https://www.mpm.go.kr"
    LIST_URL = "https://www.mpm.go.kr/mpm/comm/newsPress/newsPressRelease/"

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
        params = {"pageIndex": page}
        resp = self.fetch(self.LIST_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        rows = soup.select("table.bbsList tbody tr")
        for row in rows:
            try:
                title_td = row.select_one("td.title")
                if not title_td:
                    continue
                link_tag = title_td.select_one("a")
                if not link_tag:
                    continue
                title = link_tag.get_text(strip=True)
                if not self.matches_keyword(title):
                    continue

                href = link_tag.get("href", "")
                if href and not href.startswith("http"):
                    href = self.BASE_URL + href

                date_td = row.select_one("td.date")
                date = date_td.get_text(strip=True) if date_td else ""

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
