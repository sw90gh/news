import logging
from urllib.parse import quote
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AssemblyScraper(BaseScraper):
    """열린국회정보 - 의안 검색 스크래퍼"""

    SOURCE_NAME = "열린국회정보"
    SEARCH_URL = "https://likms.assembly.go.kr/bill/main.do"

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
        search_url = "https://likms.assembly.go.kr/bill/billSearchPage.do"
        params = {
            "billName": term,
            "pageSize": "20",
            "start_age": "22",
        }
        resp = self.fetch(search_url, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        rows = soup.select("table tbody tr")
        for row in rows[:15]:
            try:
                tds = row.select("td")
                if len(tds) < 3:
                    continue
                link_tag = row.select_one("a")
                if not link_tag:
                    continue
                title = link_tag.get_text(strip=True)
                if not title:
                    continue

                href = link_tag.get("href", "")
                # JavaScript 링크 처리
                if "javascript" in href.lower():
                    onclick = link_tag.get("onclick", "")
                    if onclick:
                        # billDetail 등의 함수에서 ID 추출 시도
                        import re
                        match = re.search(r"'([A-Z0-9_]+)'", onclick)
                        if match:
                            bill_id = match.group(1)
                            href = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
                        else:
                            continue
                    else:
                        continue
                elif href and not href.startswith("http"):
                    href = "https://likms.assembly.go.kr" + href

                date = ""
                for td in tds:
                    text = td.get_text(strip=True)
                    if len(text) == 10 and (text.count("-") == 2 or text.count(".") == 2):
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
