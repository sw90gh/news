import requests
import time
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """모든 스크래퍼의 기본 클래스"""

    SOURCE_NAME = "Unknown"

    def __init__(self, config):
        self.config = config
        self.keywords = config.get("keywords", [])
        scraper_cfg = config.get("scraper", {})
        self.delay = scraper_cfg.get("request_delay", 2)
        self.timeout = scraper_cfg.get("timeout", 30)
        self.max_retries = scraper_cfg.get("max_retries", 3)
        self.user_agent = scraper_cfg.get("user_agent", "")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Language": "ko-KR,ko;q=0.9",
        })

    def fetch(self, url, params=None):
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay)
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                logger.warning(f"[{self.SOURCE_NAME}] 요청 실패 (시도 {attempt+1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"[{self.SOURCE_NAME}] 최종 실패: {url}")
                    return None
        return None

    def matches_keyword(self, text):
        if not text:
            return False
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.keywords)

    @abstractmethod
    def scrape(self):
        """
        수집 실행. 결과는 dict 리스트로 반환:
        [{"source": str, "title": str, "url": str, "summary": str, "published_date": str}, ...]
        """
        pass
