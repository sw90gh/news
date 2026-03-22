import os
import json
import logging

logger = logging.getLogger(__name__)


def summarize_articles(articles):
    """기사 목록을 Claude API로 주제별 그룹핑 + 브리핑 요약 생성.

    Returns:
        {
            "briefing": "전체 브리핑 요약 텍스트",
            "groups": [
                {"name": "그룹명", "indices": [0, 1, 2]},
                ...
            ]
        }
        실패 시 None 반환.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY가 설정되지 않아 요약을 건너뜁니다.")
        return None

    if not articles:
        return None

    # 기사 목록을 텍스트로 구성
    article_lines = []
    for i, a in enumerate(articles):
        line = f"[{i}] [{a.get('source', '')}] {a['title']}"
        if a.get("summary"):
            line += f" — {a['summary'][:150]}"
        article_lines.append(line)

    articles_text = "\n".join(article_lines)

    prompt = f"""아래는 오늘 수집된 뉴스 기사 목록입니다. 두 가지 작업을 해주세요.

1. **브리핑 요약**: 전체 기사를 읽고, 오늘의 주요 동향을 3~5문장으로 요약해주세요.
   - 핵심 이슈가 무엇인지, 어떤 흐름인지 한눈에 파악할 수 있도록 작성
   - 격식체 사용

2. **주제별 그룹핑**: 비슷한 주제/테마의 기사들을 묶어주세요.
   - 각 그룹에 직관적인 이름을 붙여주세요 (예: "공공기관 증원 논의", "K-water 경영 현황")
   - 모든 기사가 반드시 하나의 그룹에 포함되어야 합니다
   - 그룹은 2~6개 정도로 적절히 나눠주세요
   - 혼자만 있는 기사는 "기타 동향"으로 묶어주세요

기사 목록:
{articles_text}

반드시 아래 JSON 형식으로만 응답해주세요. 다른 텍스트 없이 JSON만 출력하세요.
{{
  "briefing": "브리핑 요약 텍스트",
  "groups": [
    {{"name": "그룹명", "indices": [0, 1, 2]}},
    ...
  ]
}}"""

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        result_text = response.content[0].text.strip()
        # JSON 블록 추출 (```json ... ``` 감싸진 경우 대비)
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)
        logger.info(f"AI 요약 완료: {len(result.get('groups', []))}개 그룹")
        return result

    except Exception as e:
        logger.error(f"AI 요약 실패: {e}")
        return None
