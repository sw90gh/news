import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


CATEGORY_ORDER = {
    "법령/입법": ["국가법령정보센터", "열린국회정보"],
    "정부 정책/보도자료": ["기획재정부", "행정안전부", "인사혁신처", "정책브리핑"],
    "뉴스": [],
}


def _article_row_html(a):
    """단일 기사를 HTML 행으로 변환"""
    summary_html = ""
    if a.get("summary"):
        summary_html = f"<br><span style='color:#555;font-size:13px;'>{a['summary']}</span>"
    return f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 16px;">
                <span style="background:#e8f0fe;color:#1a73e8;padding:2px 8px;border-radius:4px;font-size:11px;margin-right:8px;">
                    {a['source']}
                </span>
                <a href="{a['url']}" style="color:#1a0dab;text-decoration:none;font-size:14px;font-weight:bold;">
                    {a['title']}
                </a>
                <br>
                <span style="color:#666;font-size:12px;">{a.get('published_date', '')}</span>
                {summary_html}
            </td>
        </tr>"""


def _group_header_html(name, color="#1a73e8"):
    return f"""
        <tr>
            <td style="background:{color};color:#fff;padding:10px 16px;font-size:14px;font-weight:bold;">
                {name}
            </td>
        </tr>"""


def _build_grouped_rows(articles, summary_result):
    """AI 그룹핑 결과로 기사를 주제별로 렌더링"""
    rows = []
    grouped_indices = set()
    colors = ["#1a73e8", "#0d7c66", "#6a1b9a", "#c62828", "#ef6c00", "#37474f"]

    for i, group in enumerate(summary_result.get("groups", [])):
        indices = group.get("indices", [])
        group_articles = [articles[idx] for idx in indices if idx < len(articles)]
        if not group_articles:
            continue
        grouped_indices.update(indices)
        color = colors[i % len(colors)]
        rows.append(_group_header_html(f"{group['name']} ({len(group_articles)}건)", color))
        for a in group_articles:
            rows.append(_article_row_html(a))

    # 그룹에 포함되지 않은 기사 처리
    ungrouped = [a for i, a in enumerate(articles) if i not in grouped_indices]
    if ungrouped:
        rows.append(_group_header_html(f"기타 ({len(ungrouped)}건)", "#5f6368"))
        for a in ungrouped:
            rows.append(_article_row_html(a))

    return "\n".join(rows)


def _build_source_rows(articles):
    """기존 소스별 분류 (AI 요약 실패 시 폴백)"""
    grouped = {}
    for a in articles:
        src = a.get("source", "기타")
        grouped.setdefault(src, []).append(a)

    rows = []
    for category, sources in CATEGORY_ORDER.items():
        category_articles = []
        for src in sources:
            category_articles.extend(grouped.pop(src, []))
        if not category_articles:
            continue
        rows.append(_group_header_html(category))
        for a in category_articles:
            rows.append(_article_row_html(a))

    for src, items in grouped.items():
        rows.append(_group_header_html(src, "#5f6368"))
        for a in items:
            rows.append(_article_row_html(a))

    return "\n".join(rows)


def build_html(today_articles, older_articles, summary_result=None):
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(today_articles) + len(older_articles)

    # 브리핑 요약 섹션
    if summary_result and summary_result.get("briefing"):
        briefing_text = summary_result["briefing"].replace("\n", "<br>")
        briefing_section = f"""
    <tr>
        <td style="background:#f0f4ff;padding:20px 16px;border-bottom:2px solid #1a73e8;">
            <div style="font-size:15px;font-weight:bold;color:#0d47a1;margin-bottom:10px;">&#128214; 오늘의 브리핑</div>
            <div style="font-size:14px;color:#333;line-height:1.7;">{briefing_text}</div>
        </td>
    </tr>"""
    else:
        briefing_section = ""

    # 오늘의 새 기사 섹션
    if today_articles:
        if summary_result and summary_result.get("groups"):
            today_rows = _build_grouped_rows(today_articles, summary_result)
        else:
            today_rows = _build_source_rows(today_articles)
        today_section = f"""
    <tr>
        <td style="background:#0d47a1;color:#fff;padding:16px;font-size:18px;font-weight:bold;">
            &#11088; 오늘의 새 기사 ({len(today_articles)}건)
        </td>
    </tr>
    {today_rows}"""
    else:
        today_section = """
    <tr>
        <td style="background:#0d47a1;color:#fff;padding:16px;font-size:18px;font-weight:bold;">
            오늘의 새 기사
        </td>
    </tr>
    <tr>
        <td style="padding:20px 16px;text-align:center;color:#999;font-size:14px;">
            오늘 새로 수집된 기사가 없습니다.
        </td>
    </tr>"""

    # 이전 미발송 기사 섹션
    if older_articles:
        older_rows = _build_source_rows(older_articles)
        older_section = f"""
    <tr>
        <td style="background:#78909c;color:#fff;padding:14px 16px;font-size:16px;font-weight:bold;">
            &#128196; 이전 미발송 기사 ({len(older_articles)}건)
        </td>
    </tr>
    {older_rows}"""
    else:
        older_section = ""

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:'맑은 고딕',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    <tr>
        <td style="background:#1a73e8;padding:24px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:22px;">K-water 정원 뉴스 브리핑</h1>
            <p style="color:#c4d7f5;margin:8px 0 0;font-size:14px;">{today} | 새 기사 {len(today_articles)}건 | 총 {total}건</p>
        </td>
    </tr>
    {briefing_section}
    {today_section}
    {older_section}
    <tr>
        <td style="background:#f5f5f5;padding:16px;text-align:center;color:#999;font-size:12px;">
            본 메일은 자동 수집 시스템에 의해 발송되었습니다.<br>
            수집 소스: 국가법령정보센터, 기획재정부, 행정안전부, 인사혁신처, 열린국회정보, 정책브리핑, 구글뉴스
        </td>
    </tr>
</table>
</body>
</html>"""
    return html


def send_email(config, today_articles, older_articles, summary_result=None):
    total = len(today_articles) + len(older_articles)
    if total == 0:
        logger.info("발송할 기사가 없습니다.")
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
    subject = f"[K-water 정원] 뉴스 브리핑 ({today}) - 새 기사 {len(today_articles)}건"

    html = build_html(today_articles, older_articles, summary_result)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info(f"이메일 발송 완료: 새 기사 {len(today_articles)}건, 이전 미발송 {len(older_articles)}건 -> {recipients}")
        return True
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        return False
