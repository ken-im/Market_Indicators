#!/usr/bin/env python3
"""
Market Indicators Dashboard Generator

시장지표 데이터를 수집하고 독립 실행 가능한 HTML 대시보드를 생성합니다.

Usage:
    python src/generate.py
    python src/generate.py --from 20200101 --to 20241231
    python src/generate.py --from 20200101 --output my_dashboard.html
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import FinanceDataReader as fdr


INDICATORS = [
    {"symbol": "KS11",    "fetch": "^KS11",  "name": "KOSPI 지수",     "desc": "코스피 종합지수"},
    {"symbol": "KQ11",    "fetch": "^KQ11",  "name": "KOSDAQ 지수",    "desc": "코스닥 종합지수"},
    {"symbol": "KS200",   "fetch": "^KS200", "name": "KOSPI 200",     "desc": "코스피 200개 기업 지수"},
    {"symbol": "DJI",     "fetch": "DJI",    "name": "다우존스 지수",   "desc": "미국 우량주 30개 종목"},
    {"symbol": "IXIC",    "fetch": "IXIC",   "name": "나스닥 종합지수", "desc": "미국 기술주 중심"},
    {"symbol": "US500",   "fetch": "US500",  "name": "S&P 500 지수",   "desc": "미국 대표 500개 기업"},
    {"symbol": "VIX",     "fetch": "VIX",    "name": "공포 지수",       "desc": "S&P 500 변동성 지수"},
    {"symbol": "JP225",   "fetch": "^N225",  "name": "닛케이 225",     "desc": "일본 대표 지수"},
    {"symbol": "SSEC",    "fetch": "SSEC",   "name": "상해 종합지수",   "desc": "중국 본토 시장"},
    {"symbol": "HSI",     "fetch": "HSI",    "name": "항셍 지수",       "desc": "홍콩 시장"},
    {"symbol": "GC",      "fetch": "GC=F",   "name": "금 선물",        "desc": "금 선물"},
    {"symbol": "CL",      "fetch": "CL",     "name": "WTI 선물",       "desc": "WTI 선물"},
    {"symbol": "BTC/USD", "fetch": "BTC/USD","name": "비트코인/달러",   "desc": "비트코인 달러 가격"},
    {"symbol": "ETH/USD", "fetch": "ETH/USD","name": "이더리움/달러",   "desc": "이더리움 달러 가격"},
]

COLORS = [
    "#4e9af1", "#6af178", "#f1a34e", "#f14e4e",
    "#9b59b6", "#1abc9c", "#e74c3c", "#f39c12",
    "#3498db", "#2ecc71", "#e67e22", "#95a5a6",
    "#f8c471", "#82e0aa",
]

DEFAULT_SELECTED = {"KS11", "US500"}
DEFAULT_FROM = "19900101"


def parse_args():
    today = datetime.today().strftime("%Y%m%d")
    parser = argparse.ArgumentParser(
        description="Market Indicators Dashboard Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--from", dest="from_date", default=DEFAULT_FROM, metavar="YYYYMMDD",
        help=f"조회 시작일 (기본값: {DEFAULT_FROM})",
    )
    parser.add_argument(
        "--to", dest="to_date", default=today, metavar="YYYYMMDD",
        help=f"조회 종료일 (기본값: 오늘, {today})",
    )
    parser.add_argument(
        "--output", default="index.html", metavar="FILE",
        help="출력 HTML 파일 경로 (기본값: index.html)",
    )
    return parser.parse_args()


def fetch_data(from_date: str, to_date: str) -> dict:
    """모든 시장지표 데이터를 FinanceDataReader로 수집합니다."""
    results = {}
    total = len(INDICATORS)

    for i, ind in enumerate(INDICATORS, 1):
        symbol = ind["symbol"]
        fetch  = ind.get("fetch", symbol)
        print(f"  [{i:2d}/{total}] {symbol:<10} ({ind['name']}) ... ", end="", flush=True)
        try:
            df = fdr.DataReader(fetch, from_date, to_date)
            if df is None or df.empty:
                print("데이터 없음")
                continue

            col = "Close" if "Close" in df.columns else df.columns[0]
            series = df[col].dropna()
            series.index = pd.to_datetime(series.index)
            series = series.sort_index()

            results[symbol] = series
            print(f"완료 ({len(series):,}건)")
        except Exception as e:
            print(f"실패 - {e}")

    return results


def normalize(series: pd.Series) -> pd.Series:
    """첫 번째 유효값을 기준(100)으로 정규화합니다."""
    series = series.dropna()
    if series.empty:
        return series
    first = series.iloc[0]
    if first == 0:
        return series
    return (series / first) * 100.0


def build_traces(data: dict) -> list:
    """Plotly에 전달할 trace 데이터 목록을 구성합니다."""
    traces = []
    for i, ind in enumerate(INDICATORS):
        symbol = ind["symbol"]
        color = COLORS[i % len(COLORS)]
        available = symbol in data

        if available:
            raw = data[symbol]
            series = normalize(raw)
            x_vals = [d.strftime("%Y-%m-%d") for d in series.index]
            y_vals = [round(float(v), 4) for v in series.values]
            date_from = raw.index[0].strftime("%Y-%m-%d")
            date_to   = raw.index[-1].strftime("%Y-%m-%d")
            count     = len(raw)
        else:
            x_vals, y_vals = [], []
            date_from = date_to = "-"
            count = 0

        traces.append({
            "symbol":    symbol,
            "name":      ind["name"],
            "desc":      ind["desc"],
            "color":     color,
            "default":   symbol in DEFAULT_SELECTED,
            "available": available,
            "date_from": date_from,
            "date_to":   date_to,
            "count":     count,
            "x": x_vals,
            "y": y_vals,
        })
    return traces


def generate_html(traces: list, from_date: str, to_date: str, output_path: str):
    """수집된 데이터를 바탕으로 독립 실행 가능한 HTML 파일을 생성합니다."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    traces_json = json.dumps(traces, ensure_ascii=False, separators=(",", ":"))

    period_label = f"{from_date[:4]}.{from_date[4:6]}.{from_date[6:]} ~ {to_date[:4]}.{to_date[4:6]}.{to_date[6:]}"

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Market Indicators Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:       #0d1117;
      --surface:  #161b22;
      --surface2: #21262d;
      --border:   #30363d;
      --text:     #e6edf3;
      --muted:    #8b949e;
      --accent:   #58a6ff;
    }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                   'Noto Sans KR', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* ── Header ── */
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 18px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    header h1 {{ font-size: 1.35rem; font-weight: 700; letter-spacing: -0.3px; }}
    .header-sub {{ font-size: 0.82rem; color: var(--muted); margin-top: 3px; }}
    .badge {{
      background: var(--accent);
      color: #0d1117;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      white-space: nowrap;
    }}

    /* ── Main layout: selector(left) + chart(right) ── */
    main {{
      flex: 1;
      padding: 18px 24px;
      max-width: 1800px;
      width: 100%;
      margin: 0 auto;
      display: flex;
      gap: 18px;
      align-items: flex-start;
    }}
    .sel-panel {{
      width: 420px;
      flex-shrink: 0;
    }}
    .chart-panel {{
      flex: 1;
      min-width: 0;
    }}

    /* ── Card ── */
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
    }}

    /* ── Chart card ── */
    .chart-card {{
      overflow: hidden;
    }}
    .chart-toolbar {{
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 6px;
    }}
    .chart-body {{ position: relative; padding: 12px 14px 8px; }}
    #chart {{ width: 100%; height: 580px; }}
    .no-sel {{
      display: none;
      position: absolute;
      inset: 0;
      align-items: center;
      justify-content: center;
      font-size: 0.95rem;
      color: var(--muted);
      pointer-events: none;
    }}

    /* ── Theme toggle ── */
    .theme-label {{
      font-size: 0.72rem;
      color: var(--muted);
      margin-right: 2px;
    }}
    .theme-group {{
      display: flex;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }}
    .theme-btn {{
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 4px 12px;
      font-size: 0.74rem;
      color: var(--muted);
      background: transparent;
      border: none;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      white-space: nowrap;
    }}
    .theme-btn.active {{
      background: var(--accent);
      color: #0d1117;
      font-weight: 600;
    }}
    .theme-btn:not(.active):hover {{ color: var(--text); }}

    /* ── Selector card ── */
    .sel-card {{ overflow: hidden; }}
    .sel-header {{
      padding: 12px 14px 10px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}
    .sel-title {{
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }}
    .sel-actions {{ display: flex; gap: 5px; }}
    .sel-actions button {{
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.71rem;
      padding: 3px 9px;
      border-radius: 5px;
      cursor: pointer;
      transition: border-color 0.15s, color 0.15s;
      white-space: nowrap;
    }}
    .sel-actions button:hover {{ border-color: var(--accent); color: var(--accent); }}

    /* ── Indicator table ── */
    .ind-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.77rem;
    }}
    .ind-table thead tr {{ border-bottom: 1px solid var(--border); }}
    .ind-table thead th {{
      padding: 6px 10px;
      font-size: 0.68rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.4px;
      text-align: left;
      white-space: nowrap;
    }}
    .ind-table thead th.num {{ text-align: right; }}
    .ind-table tbody tr {{
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      transition: background 0.12s;
    }}
    .ind-table tbody tr:last-child {{ border-bottom: none; }}
    .ind-table tbody tr:hover:not(.unavail) {{ background: var(--surface2); }}
    .ind-table tbody tr.active {{
      background: color-mix(in srgb, var(--row-color) 10%, var(--surface));
    }}
    .ind-table tbody tr.unavail {{ opacity: 0.35; cursor: not-allowed; }}
    .ind-table td {{ padding: 6px 10px; vertical-align: middle; }}
    .td-check {{ width: 30px; text-align: center; }}
    .color-dot {{
      display: inline-block;
      width: 9px; height: 9px;
      border-radius: 50%;
      vertical-align: middle;
    }}
    .check-box {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px; height: 14px;
      border: 1.5px solid var(--border);
      border-radius: 3px;
      transition: border-color 0.12s, background 0.12s;
      flex-shrink: 0;
    }}
    tr.active .check-box {{ background: var(--row-color); border-color: var(--row-color); }}
    .check-box svg {{ display: none; }}
    tr.active .check-box svg {{ display: block; }}
    .td-sym  {{ font-family: monospace; font-size: 0.73rem; color: var(--muted); white-space: nowrap; }}
    .td-name {{ font-weight: 500; white-space: nowrap; }}
    .td-date {{ color: var(--muted); font-size: 0.7rem; white-space: nowrap; font-variant-numeric: tabular-nums; }}
    .td-count {{ text-align: right; color: var(--muted); font-size: 0.7rem; font-variant-numeric: tabular-nums; white-space: nowrap; }}
    .td-unavail {{ color: var(--muted); font-size: 0.68rem; font-style: italic; }}

    /* ── Footer ── */
    footer {{
      background: var(--surface);
      border-top: 1px solid var(--border);
      padding: 12px 24px;
      font-size: 0.74rem;
      color: var(--muted);
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
    }}

    /* ── Responsive ── */
    @media (max-width: 1100px) {{
      main {{ flex-direction: column; padding: 14px; }}
      .sel-panel {{ width: 100%; }}
      #chart {{ height: 420px; }}
    }}
    @media (max-width: 640px) {{
      header {{ padding: 14px 16px; }}
      header h1 {{ font-size: 1.1rem; }}
      footer {{ padding: 12px 16px; }}
      #chart {{ height: 340px; }}
    }}
  </style>
</head>
<body>

<header>
  <div>
    <h1>Market Indicators Dashboard</h1>
    <div class="header-sub">시장지표 대시보드 &nbsp;·&nbsp; {period_label}</div>
  </div>
  <span class="badge">정규화 비교</span>
</header>

<main>
  <!-- 좌측: 지표 선택 테이블 -->
  <div class="sel-panel">
    <div class="card sel-card">
      <div class="sel-header">
        <span class="sel-title">시장지표 선택</span>
        <div class="sel-actions">
          <button onclick="selectAll()">전체</button>
          <button onclick="selectNone()">해제</button>
          <button onclick="selectDefault()">기본값</button>
        </div>
      </div>
      <table class="ind-table">
        <thead>
          <tr>
            <th class="td-check"></th>
            <th>Symbol</th>
            <th>지수명</th>
            <th>From</th>
            <th>To</th>
            <th class="num">건수</th>
          </tr>
        </thead>
        <tbody id="ind-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- 우측: 차트 -->
  <div class="chart-panel">
    <div class="card chart-card">
      <div class="chart-toolbar">
        <span class="theme-label">차트 배경</span>
        <div class="theme-group">
          <button class="theme-btn active" id="btn-dark"  onclick="setTheme('dark')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/>
            </svg>
            Dark
          </button>
          <button class="theme-btn" id="btn-light" onclick="setTheme('light')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
            Light
          </button>
        </div>
      </div>
      <div class="chart-body">
        <div id="chart"></div>
        <div class="no-sel" id="no-sel">지표를 하나 이상 선택해주세요.</div>
      </div>
    </div>
  </div>
</main>

<footer>
  <span>데이터 출처: FinanceDataReader (Python)</span>
  <span>생성일자: {generated_at}</span>
</footer>

<script>
const TRACES = {traces_json};
const selected = new Set(TRACES.filter(t => t.default && t.available).map(t => t.symbol));

/* ── 테이블 렌더링 ── */
function buildTable() {{
  const tbody = document.getElementById('ind-tbody');
  TRACES.forEach(t => {{
    const tr = document.createElement('tr');
    tr.id = 'row_' + t.symbol.replace('/', '_');
    tr.style.setProperty('--row-color', t.color);
    if (!t.available) tr.classList.add('unavail');
    if (selected.has(t.symbol)) tr.classList.add('active');

    if (t.available) {{
      tr.innerHTML = `
        <td class="td-check">
          <div style="display:flex;align-items:center;gap:4px;justify-content:center">
            <span class="check-box">
              <svg width="9" height="7" viewBox="0 0 9 7" fill="none">
                <polyline points="1,3.5 3.5,6 8,1" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
            <span class="color-dot" style="background:${{t.color}}"></span>
          </div>
        </td>
        <td class="td-sym">${{t.symbol}}</td>
        <td class="td-name">${{t.name}}</td>
        <td class="td-date">${{t.date_from}}</td>
        <td class="td-date">${{t.date_to}}</td>
        <td class="td-count">${{t.count.toLocaleString()}}</td>`;
      tr.addEventListener('click', () => toggle(t.symbol));
    }} else {{
      tr.innerHTML = `
        <td class="td-check">
          <span class="color-dot" style="background:${{t.color}};opacity:0.4"></span>
        </td>
        <td class="td-sym">${{t.symbol}}</td>
        <td class="td-name">${{t.name}}</td>
        <td colspan="3" class="td-unavail">데이터 없음</td>`;
    }}
    tbody.appendChild(tr);
  }});
}}

function toggle(sym) {{
  selected.has(sym) ? selected.delete(sym) : selected.add(sym);
  document.getElementById('row_' + sym.replace('/', '_')).classList.toggle('active', selected.has(sym));
  render();
}}
function selectAll() {{
  TRACES.filter(t => t.available).forEach(t => {{
    selected.add(t.symbol);
    document.getElementById('row_' + t.symbol.replace('/', '_')).classList.add('active');
  }});
  render();
}}
function selectNone() {{
  selected.clear();
  document.querySelectorAll('#ind-tbody tr').forEach(tr => tr.classList.remove('active'));
  render();
}}
function selectDefault() {{
  selectNone();
  TRACES.filter(t => t.default && t.available).forEach(t => {{
    selected.add(t.symbol);
    document.getElementById('row_' + t.symbol.replace('/', '_')).classList.add('active');
  }});
  render();
}}

/* ── 테마 설정 ── */
const THEMES = {{
  dark: {{
    paper_bgcolor: '#161b22',
    plot_bgcolor:  '#0d1117',
    font_color:    '#e6edf3',
    grid_color:    '#21262d',
    line_color:    '#30363d',
    legend_bg:     'rgba(22,27,34,0.88)',
    hover_bg:      '#21262d',
    hover_font:    '#e6edf3',
    slider_bg:     '#161b22',
  }},
  light: {{
    paper_bgcolor: '#ffffff',
    plot_bgcolor:  '#f6f8fa',
    font_color:    '#24292f',
    grid_color:    '#e1e4e8',
    line_color:    '#d0d7de',
    legend_bg:     'rgba(255,255,255,0.92)',
    hover_bg:      '#ffffff',
    hover_font:    '#24292f',
    slider_bg:     '#f6f8fa',
  }},
}};
let currentTheme = 'dark';

function setTheme(name) {{
  currentTheme = name;
  document.getElementById('btn-dark').classList.toggle('active',  name === 'dark');
  document.getElementById('btn-light').classList.toggle('active', name === 'light');
  render();
}}

/* ── Plotly 렌더링 ── */
let initialized = false;

function render() {{
  const active = TRACES.filter(t => selected.has(t.symbol));
  const noSel  = document.getElementById('no-sel');

  if (active.length === 0) {{
    noSel.style.display = 'flex';
    if (initialized) Plotly.react('chart', [], layout());
    return;
  }}
  noSel.style.display = 'none';

  const plotData = active.map(t => ({{
    x: t.x,
    y: t.y,
    name: t.name,
    type: 'scatter',
    mode: 'lines',
    line: {{ color: t.color, width: 1.8 }},
    hovertemplate: '<b>%{{fullData.name}}</b><br>날짜: %{{x}}<br>정규화: %{{y:.2f}}<extra></extra>',
  }}));

  Plotly.react('chart', plotData, layout(), config());
  initialized = true;
}}

function layout() {{
  const t = THEMES[currentTheme];
  return {{
    paper_bgcolor: t.paper_bgcolor,
    plot_bgcolor:  t.plot_bgcolor,
    font: {{ color: t.font_color, family: "-apple-system, 'Segoe UI', Roboto, sans-serif", size: 12 }},
    xaxis: {{
      showgrid: true,
      gridcolor: t.grid_color,
      linecolor: t.line_color,
      tickcolor: t.line_color,
      tickfont:  {{ color: t.font_color }},
      title: {{ text: '날짜', standoff: 12, font: {{ color: t.font_color }} }},
      rangeslider: {{ visible: true, bgcolor: t.slider_bg, bordercolor: t.line_color, thickness: 0.06 }},
    }},
    yaxis: {{
      showgrid: true,
      gridcolor: t.grid_color,
      linecolor: t.line_color,
      tickcolor: t.line_color,
      tickfont:  {{ color: t.font_color }},
      title: {{ text: '정규화 지수 (기준: 100)', standoff: 10, font: {{ color: t.font_color }} }},
      hoverformat: '.2f',
    }},
    legend: {{
      bgcolor: t.legend_bg,
      bordercolor: t.line_color,
      borderwidth: 1,
      x: 0.01, y: 0.99,
      xanchor: 'left',
      yanchor: 'top',
      font: {{ color: t.font_color }},
    }},
    margin: {{ l: 65, r: 20, t: 16, b: 60 }},
    hovermode: 'x unified',
    hoverlabel: {{
      bgcolor: t.hover_bg,
      bordercolor: t.line_color,
      font: {{ color: t.hover_font }},
    }},
    autosize: true,
  }};
}}

function config() {{
  return {{
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['select2d', 'lasso2d'],
    displaylogo: false,
    toImageButtonOptions: {{ format: 'png', filename: 'market_indicators', scale: 2 }},
  }};
}}

buildTable();
render();
</script>

</body>
</html>
"""

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"\n  HTML 저장 완료: {out.resolve()}")
    print(f"  파일 크기: {out.stat().st_size / 1024:.1f} KB")


def main():
    args = parse_args()
    print("=" * 55)
    print("  Market Indicators Dashboard Generator")
    print("=" * 55)
    print(f"  조회 기간: {args.from_date} ~ {args.to_date}")
    print(f"  출력 파일: {args.output}")
    print("-" * 55)
    print("  데이터 수집 중...")

    data = fetch_data(args.from_date, args.to_date)
    success = sum(1 for s in [ind["symbol"] for ind in INDICATORS] if s in data)
    print(f"\n  수집 완료: {success}/{len(INDICATORS)}개 지표")
    print("-" * 55)
    print("  HTML 생성 중...")

    traces = build_traces(data)
    generate_html(traces, args.from_date, args.to_date, args.output)
    print("=" * 55)


if __name__ == "__main__":
    main()
