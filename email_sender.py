import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


def build_html(articles):
    today = datetime.now().strftime("%Y-%m-%d")

    # 소스별 그룹핑
    grouped = {}
    for a in articles:
        src = a.get("source", "기타")
        grouped.setdefault(src, []).append(a)

    # 소스 카테고리 분류
    category_order = {
        "법령/입법": ["국가법령정보센터", "열린국회정보"],
        "정부 정책/보도자료": ["기획재정부", "행정안전부", "인사혁신처"],
        "뉴스": ["네이버뉴스"],
    }

    rows = []
    for category, sources in category_order.items():
        category_articles = []
        for src in sources:
            category_articles.extend(grouped.pop(src, []))
        if not category_articles:
            continue

        rows.append(f"""
        <tr>
            <td style="background:#1a73e8;color:#fff;padding:12px 16px;font-size:16px;font-weight:bold;" colspan="2">
                {category}
            </td>
        </tr>""")

        for a in category_articles:
            badge_color = "#e8f0fe"
            rows.append(f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:12px 16px;">
                <span style="background:{badge_color};color:#1a73e8;padding:2px 8px;border-radius:4px;font-size:12px;margin-right:8px;">
                    {a['source']}
                </span>
                <a href="{a['url']}" style="color:#1a0dab;text-decoration:none;font-size:14px;font-weight:bold;">
                    {a['title']}
                </a>
                <br>
                <span style="color:#666;font-size:12px;">{a.get('published_date', '')}</span>
                {"<br><span style='color:#555;font-size:13px;'>" + a['summary'] + "</span>" if a.get('summary') else ""}
            </td>
        </tr>""")

    # 미분류 소스 처리
    for src, items in grouped.items():
        rows.append(f"""
        <tr>
            <td style="background:#5f6368;color:#fff;padding:12px 16px;font-size:16px;font-weight:bold;" colspan="2">
                {src}
            </td>
        </tr>""")
        for a in items:
            rows.append(f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:12px 16px;">
                <a href="{a['url']}" style="color:#1a0dab;text-decoration:none;font-size:14px;font-weight:bold;">
                    {a['title']}
                </a>
                <br>
                <span style="color:#666;font-size:12px;">{a.get('published_date', '')}</span>
            </td>
        </tr>""")

    article_rows = "\n".join(rows)

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:'맑은 고딕',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    <tr>
        <td style="background:#1a73e8;padding:24px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:22px;">공공기관 정원 뉴스 브리핑</h1>
            <p style="color:#c4d7f5;margin:8px 0 0;font-size:14px;">{today} | 총 {len(articles)}건</p>
        </td>
    </tr>
    {article_rows}
    <tr>
        <td style="background:#f5f5f5;padding:16px;text-align:center;color:#999;font-size:12px;">
            본 메일은 자동 수집 시스템에 의해 발송되었습니다.<br>
            수집 소스: 국가법령정보센터, 기획재정부, 행정안전부, 인사혁신처, 열린국회정보, 네이버뉴스
        </td>
    </tr>
</table>
</body>
</html>"""
    return html


def send_email(config, articles):
    if not articles:
        logger.info("발송할 새 기사가 없습니다.")
        return False

    email_cfg = config.get("email", {})
    sender = email_cfg.get("sender", "")
    password = email_cfg.get("password", "")
    recipients = email_cfg.get("recipients", [])
    recipients = [r for r in recipients if r]

    if not sender or not password or not recipients:
        logger.error("이메일 설정이 불완전합니다. config.yaml을 확인하세요.")
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"[공공기관 정원] 뉴스 브리핑 ({today}) - {len(articles)}건"

    html = build_html(articles)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info(f"이메일 발송 완료: {len(articles)}건 -> {recipients}")
        return True
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        return False
