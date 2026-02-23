import logging
import xml.etree.ElementTree as ET
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LawScraper(BaseScraper):
    """국가법령정보센터 Open API 기반 법령 검색"""

    SOURCE_NAME = "국가법령정보센터"
    API_URL = "http://www.law.go.kr/DRF/lawSearch.do"

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
            "OC": "test",
            "target": "law",
            "type": "XML",
            "query": term,
            "display": "20",
            "sort": "ddes",
        }
        resp = self.fetch(self.API_URL, params=params)
        if not resp:
            return []

        results = []
        try:
            root = ET.fromstring(resp.content)
            for law in root.findall(".//law"):
                law_name = law.findtext("법령명한글", "")
                law_id = law.findtext("법령일련번호", "")
                ministry = law.findtext("소관부처명", "")
                enforcement_date = law.findtext("시행일자", "")
                detail_link = law.findtext("법령상세링크", "")

                url = f"https://www.law.go.kr{detail_link}" if detail_link else ""

                results.append({
                    "source": self.SOURCE_NAME,
                    "title": law_name,
                    "url": url,
                    "summary": f"소관: {ministry} | 검색어: {term}",
                    "published_date": enforcement_date,
                })
        except ET.ParseError as e:
            logger.error(f"[{self.SOURCE_NAME}] XML 파싱 오류: {e}")

        logger.info(f"[{self.SOURCE_NAME}] '{term}' -> {len(results)}건 수집")
        return results
