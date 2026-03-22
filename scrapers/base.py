import requests
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

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
        self.collection_days = config.get("collection_days", 7)
        ctx = config.get("context_filter", {})
        self.ambiguous_keywords = [k.lower() for k in ctx.get("ambiguous_keywords", [])]
        self.exclude_words = [w.lower() for w in ctx.get("exclude_words", [])]
        self.require_words = [w.lower() for w in ctx.get("require_words", [])]
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

    def get_matched_keyword(self, text):
        """매칭된 첫 번째 키워드를 반환. 매칭 없으면 빈 문자열."""
        if not text:
            return ""
        text_lower = text.lower()
        for kw in self.keywords:
            if kw in text_lower:
                return kw
        return ""

    def passes_context_filter(self, text, matched_keyword=""):
        """문맥 필터링. 모호한 키워드로 매칭된 기사만 필터링 적용."""
        if not matched_keyword or matched_keyword.lower() not in self.ambiguous_keywords:
            return True
        if not text:
            return False
        text_lower = text.lower()
        # 제외 키워드에 걸리면 바로 제외
        if any(w in text_lower for w in self.exclude_words):
            return False
        # 문맥 키워드가 하나 이상 있어야 통과
        if self.require_words and not any(w in text_lower for w in self.require_words):
            return False
        return True

    def is_within_period(self, date_str):
        """published_date가 collection_days 이내인지 확인. 파싱 실패 시 True(통과)"""
        if not date_str:
            return True
        cutoff = datetime.now() - timedelta(days=self.collection_days)
        try:
            # RFC 2822 형식 (RSS 표준: "Mon, 01 Jan 2024 00:00:00 GMT")
            dt = parsedate_to_datetime(date_str)
            dt = dt.replace(tzinfo=None)
            return dt >= cutoff
        except Exception:
            pass
        # YYYY-MM-DD 또는 YYYYMMDD 형식
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y%m%d"):
            try:
                dt = datetime.strptime(date_str.strip()[:10], fmt)
                return dt >= cutoff
            except ValueError:
                continue
        return True

    @abstractmethod
    def scrape(self):
        """
        수집 실행. 결과는 dict 리스트로 반환:
        [{"source": str, "title": str, "url": str, "summary": str, "published_date": str}, ...]
        """
        pass
