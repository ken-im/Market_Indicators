# Market Indicators Dashboard

각국 주요 시장지표를 수집하고 정규화 비교 그래프를 단일 HTML 파일로 생성합니다.  
생성된 `index.html`은 GitHub Pages를 통해 정적 웹 페이지로 배포할 수 있습니다.

## 지원 지표

| Symbol | 지수 명칭 | 설명 |
|--------|----------|------|
| KS11 | KOSPI 지수 | 코스피 종합지수 |
| KQ11 | KOSDAQ 지수 | 코스닥 종합지수 |
| KS200 | KOSPI 200 | 코스피 200개 기업 지수 |
| DJI | 다우존스 지수 | 미국 우량주 30개 종목 |
| IXIC | 나스닥 종합지수 | 미국 기술주 중심 |
| US500 | S&P 500 지수 | 미국 대표 500개 기업 |
| VIX | 공포 지수 | S&P 500 변동성 지수 |
| JP225 | 닛케이 225 | 일본 대표 지수 |
| SSEC | 상해 종합지수 | 중국 본토 시장 |
| HSI | 항셍 지수 | 홍콩 시장 |
| GC | 금 선물 | 금 선물 |
| CL | WTI 선물 | WTI 선물 |
| BTC/USD | 비트코인/달러 | 비트코인 달러 가격 |
| ETH/USD | 이더리움/달러 | 이더리움 달러 가격 |

## 설치

```bash
# 1. 가상환경 생성
python -m venv .venv

# 2. 가상환경 활성화
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd)
.venv\Scripts\activate.bat
# macOS / Linux
source .venv/bin/activate

# 3. 패키지 설치
pip install -r requirements.txt
```

## 사용법

```bash
# 가상환경 활성화 후 실행

# 기본 실행 (1990-01-01 ~ 오늘, index.html 생성)
python src/generate.py

# 기간 지정
python src/generate.py --from 20200101 --to 20241231

# 출력 파일 지정
python src/generate.py --from 20200101 --output docs/dashboard.html
```

### 아규먼트

| 아규먼트 | 설명 | 기본값 |
|---------|------|--------|
| `--from` | 조회 시작일 (YYYYMMDD) | `19900101` |
| `--to` | 조회 종료일 (YYYYMMDD) | 오늘 날짜 |
| `--output` | 출력 HTML 파일 경로 | `index.html` |

## 디렉토리 구조

```
market_indicators/
├── docs/               # 문서
├── src/
│   └── generate.py     # 데이터 수집 및 HTML 생성 스크립트
├── index.html          # 생성된 대시보드 (generate.py 실행 후)
├── requirements.txt
└── README.md
```

## 기술 스택

- **데이터 수집**: [FinanceDataReader](https://github.com/FinanceData/FinanceDataReader)
- **데이터 처리**: pandas, numpy
- **시각화**: [Plotly.js](https://plotly.com/javascript/)
- **배포**: GitHub Pages (정적 HTML)

## GitHub Pages 배포

1. `python src/generate.py` 실행하여 `index.html` 생성
2. 생성된 `index.html`을 GitHub 저장소에 push
3. 저장소 Settings → Pages → `main` 브랜치 루트 경로로 설정

---

데이터 출처: FinanceDataReader
