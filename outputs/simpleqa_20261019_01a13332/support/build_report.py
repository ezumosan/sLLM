from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path('/Users/ezumo/Desktop/ai/sLLM')
RUN = ROOT / 'results/simpleqa/full_20261016_065028_354181'
OUT = ROOT / 'outputs/simpleqa_20261019_01a13332'
PDF = ROOT / 'output/pdf/simpleqa_interim_20261019.pdf'
FONT = 'ReportJP'
pdfmetrics.registerFont(TTFont(FONT, '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
INK = colors.HexColor('#26283E')
MUTED = colors.HexColor('#64687A')
GRID = colors.HexColor('#E7E8EF')
PALETTE = {'A': '#5C61F2', 'C': '#343655', 'B': '#DBDCED'}
ORDER = ['A', 'C', 'B']
LABEL = {'A': '正解', 'C': '棄権', 'B': '誤答'}
ENGLISH = {'A': 'CORRECT', 'C': 'NOT_ATTEMPTED', 'B': 'INCORRECT'}


def read_records(name):
    path = RUN / name
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


rows = read_records('dataset.jsonl')
samples = []
for filename in ('samples.jsonl', 'recovery_samples.jsonl'):
    for row in read_records(filename):
        row['source_file'] = filename
        samples.append(row)
samples.sort(key=lambda row: row['question_number'])
ids = {s['question_number'] for s in samples}
assert len(ids) == len(samples)
for s in samples:
    source = rows[s['question_number'] - 1]
    assert (s['question'], s['reference_answer']) == (source['problem'], source['answer'])
    assert s['grade'] in ORDER
    assert s['grader_response']['response']['message']['content'] == s['grade']
seed_set = {s['seed'] for s in samples}
assert len(seed_set) == 1
count = Counter(s['grade'] for s in samples)
n = len(samples)
total = len(rows)
errors = {row['question_number'] for row in read_records('recovery_errors.jsonl')} - ids
truncated = sum(s['answer_response']['response']['done_reason'] == 'length' for s in samples)
last_time = max(s['grader_response']['response']['created_at'] for s in samples)
last_jst = datetime.fromisoformat(last_time.replace('Z', '+00:00')).astimezone(ZoneInfo('Asia/Tokyo'))
data = {
    'report_date': '2026-10-19', 'latest_response_jst': last_jst.isoformat(),
    'run_id': RUN.name, 'total': total, 'graded': n, 'ungraded': total-n,
    'known_inference_errors': len(errors), 'error_question_ids': sorted(errors),
    'other_ungraded': total-n-len(errors), 'counts': dict(count),
    'fractions': {key: count[key]/n for key in ORDER},
    'attempted': count['A']+count['B'],
    'accuracy_given_attempted': count['A']/(count['A']+count['B']),
    'f_score': 2*count['A']/(n+count['A']+count['B']),
    'completion_rate': n/total, 'truncated': truncated, 'truncated_rate': truncated/n,
    'seed': next(iter(seed_set)), 'answer_model': 'phi3.5', 'grader_model': 'qwen3.5:4b',
    'answer_temperature': 0.1, 'grader_temperature': 0.0, 'num_predict': 1024,
    'source_sha256': {name: hashlib.sha256((RUN/name).read_bytes()).hexdigest()
                      for name in ('samples.jsonl','recovery_samples.jsonl','dataset.jsonl','run.json','recovery.json')},
    'records': [[s['question_number'], s['grade'], s['seed'],
                 s['answer_response']['response']['eval_count'],
                 s['answer_response']['response']['done_reason'],
                 s['grader_response']['response']['message']['content'], s['source_file']]
                for s in samples],
}
OUT.mkdir(parents=True, exist_ok=True)
PDF.parent.mkdir(parents=True, exist_ok=True)
(OUT/'support/report_data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
with (OUT/'simpleqa_summary.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['判定','採点ラベル','件数','採点済みに占める割合（%）','分母'])
    for key in ORDER:
        writer.writerow([LABEL[key], ENGLISH[key], count[key], count[key]/n*100, n])


def chart():
    d = Drawing(800, 220)
    d.add(Rect(0, 0, 800, 220, fillColor=colors.white, strokeColor=None))
    x, y, w = 110, 76, 650
    legend_positions = [110, 330, 560]
    for key, lx in zip(ORDER, legend_positions):
        d.add(Rect(lx, 184, 12, 12, fillColor=colors.HexColor(PALETTE[key]), strokeColor=None))
        d.add(String(lx+20, 184, f'{LABEL[key]}  {count[key]/n*100:.2f}%', fontName=FONT, fontSize=14, fillColor=INK))
    for tick in range(0,101,10):
        gx=x+w*tick/100
        d.add(Line(gx,y,gx,155,strokeColor=GRID,strokeWidth=0.7))
    bc=HorizontalBarChart()
    bc.x=x
    bc.y=112
    bc.width=w
    bc.height=26
    bc.data=[[count[key]/n*100] for key in ORDER]
    bc.categoryAxis.style='stacked'
    bc.categoryAxis.categoryNames=['Phi-3.5']
    bc.categoryAxis.visible=False
    bc.valueAxis.valueMin=0
    bc.valueAxis.valueMax=100
    bc.valueAxis.valueStep=25
    bc.valueAxis.visible=False
    bc.groupSpacing=0
    bc.barSpacing=0
    bc.barWidth=26
    bc.bars.strokeColor=None
    for i,key in enumerate(ORDER):
        bc.bars[i].fillColor=colors.HexColor(PALETTE[key])
    d.add(bc)
    d.add(String(x-14, 120, 'Phi-3.5', textAnchor='end', fontName=FONT, fontSize=15, fillColor=INK))
    d.add(Line(x,y,x+w,y,strokeColor=colors.HexColor('#BFC2D0'),strokeWidth=0.8))
    for tick in (0,25,50,75,100):
        d.add(String(x+w*tick/100,y-22,f'{tick:.0f}%',textAnchor='middle',fontName=FONT,fontSize=13,fillColor=MUTED))
    left=0
    for key in ORDER:
        pct=count[key]/n*100
        if key != 'A':
            d.add(String(x+w*(left+pct/2)/100,120,f'{pct:.2f}%',textAnchor='middle',fontName=FONT,fontSize=14,
                         fillColor=colors.white if key=='C' else INK))
        left+=pct
    d.add(String(x, 15, f'SimpleQA  /  採点済み n = {n:,}  /  Qwen3.5:4bによる自動採点（暫定）',
                 fontName=FONT,fontSize=12,fillColor=MUTED))
    return d


d=chart()
renderSVG.drawToFile(d, str(OUT/'simpleqa_chart.svg'))
chart_pdf=OUT/'support/chart.pdf'
c=canvas.Canvas(str(chart_pdf), pagesize=(800,220))
renderPDF.draw(d,c,0,0)
c.save()

c=canvas.Canvas(str(PDF), pagesize=A4)
c.setTitle('Phi-3.5 SimpleQA 暫定評価結果 2026-10-19')
c.setAuthor('sLLM research')
width,height=A4
margin=42
content=width-2*margin


def text(x,y,value,size=10,color=INK,align='left'):
    c.setFillColor(color)
    c.setFont(FONT,size)
    method={'left':c.drawString,'right':c.drawRightString,'center':c.drawCentredString}[align]
    method(x,y,value)


text(margin, height-57, 'Phi-3.5 / SimpleQA', 23)
text(margin,height-83,'暫定評価結果',14)
text(width-margin,height-80,'2026年10月19日',10,MUTED,'right')
c.setStrokeColor(colors.HexColor('#5C61F2'))
c.setLineWidth(1.5)
c.line(margin,height-98,width-margin,height-98)
text(margin,height-121,f'採点済み {n:,} / {total:,} 問  （{n/total*100:.2f}%）',12)
text(margin,height-141,'割合の分母は、採点が完了した3,783問。',9.5,MUTED)
c.saveState()
c.translate(margin-7,height-300)
c.scale((content+14)/800,(content+14)/800)
renderPDF.draw(d,c,0,0)
c.restoreState()

table_y=height-316
colx=[margin, margin+270, width-margin]
c.setFillColor(colors.HexColor('#F2F3F8'))
c.rect(margin,table_y-25,content,25,fill=1,stroke=0)
text(margin+12,table_y-17,'採点結果',10)
text(colx[1]+25,table_y-17,'件数',10,align='right')
text(colx[2]-12,table_y-17,'構成比',10,align='right')
for i,key in enumerate(ORDER):
    top=table_y-25-i*34
    c.setFillColor(colors.HexColor(PALETTE[key]))
    c.rect(margin+12,top-22,8,8,fill=1,stroke=0)
    text(margin+30,top-22,f'{LABEL[key]}  {ENGLISH[key]}',10)
    text(colx[1]+25,top-22,f'{count[key]:,}',11,align='right')
    text(colx[2]-12,top-22,f'{count[key]/n*100:.2f}%',11,align='right')
    c.setStrokeColor(GRID)
    c.setLineWidth(.5)
    c.line(margin,top-34,width-margin,top-34)
total_y=table_y-25-3*34
text(margin+12,total_y-23,'合計（採点済み）',10)
text(colx[1]+25,total_y-23,f'{n:,}',11,align='right')
text(colx[2]-12,total_y-23,'100.00%',11,align='right')

y=total_y-62
text(margin,y,'回答時正答率',11)
text(margin+110,y,f'{data["accuracy_given_attempted"]*100:.2f}%',18,colors.HexColor('#5C61F2'))
text(margin+210,y,'= 132 / (132 + 583)',10,MUTED)
text(margin,y-24,f'SimpleQA F-score  {data["f_score"]*100:.2f}%',10,MUTED)

y-=62
text(margin,y,'実験条件',11)
c.setStrokeColor(GRID)
c.line(margin,y-9,width-margin,y-9)
settings=[('回答モデル','phi3.5','採点モデル','qwen3.5:4b'),
          ('回答 temperature','0.1','採点 temperature','0.0'),
          ('Seed（全問共通）',str(data['seed']),'回答上限','1,024 tokens')]
for i,(a,b,e,f) in enumerate(settings):
    yy=y-29-i*22
    text(margin,yy,a,9,MUTED)
    text(margin+110,yy,b,10)
    text(margin+264,yy,e,9,MUTED)
    text(margin+375,yy,f,10)

note_y=y-105
notes=[f'未採点 {total-n:,}問：反復生成エラー {len(errors)}問、その他 {total-n-len(errors):,}問。構成比の分母から除外。',
       f'回答が出力上限に達したものは {truncated}問（採点済みの {truncated/n*100:.2f}%）。',
       'Qwen3.5:4bによる自動採点の記録値。人手検証前で、OpenAI公表値とは評価条件が異なる。']
for i,line in enumerate(notes):
    text(margin,note_y-i*17,line,8.4,MUTED)
text(margin,48,'集計元：samples.jsonl / recovery_samples.jsonl（2026年10月16日・17日実行分）',8,MUTED)
text(margin,33,f'最終採点応答：{last_jst.strftime("%Y-%m-%d %H:%M:%S")} JST',8,MUTED)
c.showPage()
c.save()
print(json.dumps({k:v for k,v in data.items() if k not in ('records','source_sha256')},ensure_ascii=False,indent=2))
print(PDF)
