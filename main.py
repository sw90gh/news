import os
import sys
import yaml
import logging
from datetime import datetime

from database import init_db, save_article, get_unsent_articles, mark_as_sent, cleanup_old_articles
from email_sender import send_email
from scrapers import ALL_SCRAPERS

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 환경변수로 이메일 설정 오버라이드 (GitHub Actions Secrets 용)
    env_sender = os.environ.get("EMAIL_SENDER")
    env_password = os.environ.get("EMAIL_PASSWORD")
    env_recipients = os.environ.get("EMAIL_RECIPIENTS")

    if env_sender:
        config["email"]["sender"] = env_sender
    if env_password:
        config["email"]["password"] = env_password
    if env_recipients:
        config["email"]["recipients"] = [r.strip() for r in env_recipients.split(",")]

    return config


def collect_articles(config):
    all_articles = []
    for scraper_cls in ALL_SCRAPERS:
        scraper_name = scraper_cls.SOURCE_NAME
        try:
            logger.info(f"--- {scraper_name} 수집 시작 ---")
            scraper = scraper_cls(config)
            articles = scraper.scrape()
            logger.info(f"--- {scraper_name} 수집 완료: {len(articles)}건 ---")
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"[{scraper_name}] 스크래퍼 실행 실패: {e}")
            continue
    return all_articles


def main():
    logger.info("=" * 60)
    logger.info(f"공공기관 정원 뉴스 수집 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 설정 로드
    config = load_config()

    # DB 초기화
    init_db()

    # 기사 수집
    articles = collect_articles(config)
    logger.info(f"총 수집 건수: {len(articles)}건")

    # DB에 신규 기사 저장
    new_count = 0
    for article in articles:
        saved = save_article(
            source=article["source"],
            title=article["title"],
            url=article["url"],
            summary=article.get("summary", ""),
            published_date=article.get("published_date", ""),
        )
        if saved:
            new_count += 1

    logger.info(f"신규 기사: {new_count}건")

    # 미발송 기사 조회 및 이메일 발송
    unsent = get_unsent_articles()
    if unsent:
        logger.info(f"미발송 기사 {len(unsent)}건 이메일 발송 시작")
        success = send_email(config, unsent)
        if success:
            ids = [a["id"] for a in unsent]
            mark_as_sent(ids)
            logger.info("이메일 발송 및 상태 업데이트 완료")
    else:
        logger.info("발송할 새 기사가 없습니다.")

    # 오래된 기사 정리
    cleanup_old_articles(days=400)

    logger.info("=" * 60)
    logger.info("수집 완료")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
