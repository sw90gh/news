import logging
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AssemblyScraper(BaseScraper):
    """열린국회정보 Open API 기반 의안 검색"""

    SOURCE_NAME = "열린국회정보"
    API_URL = "https://open.assembly.go.kr/portal/openapi/TVBPMBILL11"

    def scrape(self):
        articles = []
        search_terms = ["정원", "정부조직", "공공기관"]
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
            "Type": "json",
            "pSize": "30",
            "AGE": "22",
            "BILL_NAME": term,
        }
        resp = self.fetch(self.API_URL, params=params)
        if not resp:
            return []

        results = []
        try:
            data = resp.json()
            api_data = data.get("TVBPMBILL11", [])
            if not api_data or len(api_data) < 2:
                return []

            rows = api_data[1].get("row", [])
            for row in rows:
                bill_name = row.get("BILL_NAME", "")
                propose_dt = row.get("PROPOSE_DT", "")
                proposer = row.get("RST_PROPOSER", row.get("PROPOSER", ""))
                link = row.get("LINK_URL", "")
                proposer_kind = row.get("PROPOSER_KIND", "")
                proc_result = row.get("PROC_RESULT_CD", "계류")

                results.append({
                    "source": self.SOURCE_NAME,
                    "title": bill_name,
                    "url": link,
                    "summary": f"발의: {proposer} ({proposer_kind}) | 처리상태: {proc_result}",
                    "published_date": propose_dt,
                })
        except (ValueError, KeyError) as e:
            logger.error(f"[{self.SOURCE_NAME}] 응답 파싱 오류: {e}")

        logger.info(f"[{self.SOURCE_NAME}] '{term}' -> {len(results)}건 수집")
        return results
