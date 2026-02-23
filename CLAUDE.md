# 공공기관 정원 뉴스 스크래퍼 (News Scraper)

## 프로젝트 개요
공공기관 정원 관련 정부동향, 뉴스, 법령개정 현황을 매일 자동 수집하여 이메일로 발송하는 프로그램

## 기술 스택
- **언어**: Python 3.11+
- **이메일**: Gmail SMTP
- **스케줄링**: GitHub Actions (매일 오전 8시 KST 자동 실행, cron: `0 23 * * *` UTC)
- **DB**: SQLite (중복 제거 및 이력 관리, GitHub Actions 캐시로 유지)
- **스크래핑**: requests, beautifulsoup4, feedparser, lxml

## 데이터 소스 (공신력 있는 출처)
| 소스 | 수집 방식 | 수집 대상 |
|------|-----------|-----------|
| Google News RSS | RSS 피드 | 키워드 기반 뉴스 검색 (메인 소스) |
| 기획재정부 | RSS 피드 | 공공기관 정책/보도자료 |
| 행정안전부 | RSS 피드 | 정부조직/정원 보도자료 |
| 인사혁신처 | 웹 스크래핑 | 인사/정원 보도자료 (table.bbsList) |
| 국가법령정보센터 | Google News RSS | 법령 개정 관련 뉴스 |
| 열린국회정보 | Open API (TVBPMBILL11) | 관련 법안/의안 발의 현황 |
| 정책브리핑 (korea.kr) | RSS 피드 | 정부 정책 브리핑 |

## 키워드 (config.yaml에서 수정)
- 공공기관 정원, 정부조직 정원, 정원관리, 공무원 정원, 총정원, 정원조정, 공공기관 인력/채용
- 한국수자원공사, K-water, 수자원공사, kwater
- 윤석대, 구자영, 남영현

## 프로젝트 구조
```
news/
├── main.py                  # 메인 실행 파일
├── database.py              # SQLite DB (중복 제거/이력 관리)
├── email_sender.py          # Gmail SMTP 이메일 발송
├── config.yaml              # 설정 파일 (키워드, 이메일 등)
├── requirements.txt         # Python 패키지 의존성
├── scrapers/
│   ├── __init__.py
│   ├── base.py              # 기본 스크래퍼 클래스
│   ├── google_news.py       # Google News RSS 검색
│   ├── moef.py              # 기획재정부 RSS
│   ├── mois.py              # 행정안전부 RSS
│   ├── mpm.py               # 인사혁신처 웹 스크래핑
│   ├── law.py               # 법령 관련 Google News RSS
│   ├── assembly.py          # 열린국회정보 Open API
│   └── korea_kr.py          # 정책브리핑 RSS
└── .github/workflows/
    └── daily_news.yml       # GitHub Actions 스케줄링
```

## GitHub Actions 설정
리포지토리 Settings > Secrets and variables > Actions:
- `EMAIL_SENDER`: 발신 Gmail 주소
- `EMAIL_PASSWORD`: Gmail 앱 비밀번호 (Google 계정 > 보안 > 앱 비밀번호)
- `EMAIL_RECIPIENTS`: 수신자 이메일 (쉼표 구분, 여러 명 가능)

## 키워드 수정 방법
`config.yaml`의 `keywords` 항목을 수정 후 커밋 & 푸시하면 다음 실행부터 반영

## 현재 상태
- [x] 요구사항 정의 완료
- [x] 기술 스택 결정
- [x] 데이터 소스 선정 및 수집 방식 확정
- [x] 스크래퍼 모듈 구현 (7개 소스)
- [x] 이메일 발송 모듈 구현 (HTML 포맷, 카테고리별 분류)
- [x] 데이터베이스 모듈 구현
- [x] 메인 실행 파일 구현
- [x] GitHub Actions 워크플로우 설정
- [x] GitHub Secrets 설정 완료
- [x] 실제 환경 테스트 완료 (473건 수집, 이메일 발송 확인)
