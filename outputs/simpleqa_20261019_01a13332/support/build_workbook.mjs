import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const out='/Users/ezumo/Desktop/ai/sLLM/outputs/simpleqa_20261019_01a13332';
const data=JSON.parse(await fs.readFile(`${out}/support/report_data.json`,'utf8'));
const wb=Workbook.create();
const summary=wb.worksheets.add('集計');
const records=wb.worksheets.add('採点記録');
for(const sheet of [summary,records]) sheet.showGridLines=false;
summary.tabColor='#343655';
const font={name:'Arial Unicode MS',size:11,color:'#26283E'};
summary.getRange('A1:F29').format.font=font;
summary.getRange('A1:F29').format.rowHeight=25;
summary.getRange('A1:F29').format.verticalAlignment='center';
for(const [col,width] of [['A',34],['B',15],['C',16],['D',4],['E',49],['F',23]]){
  summary.getRange(`${col}1:${col}29`).format.columnWidth=width;
}
summary.getRange('A2').values=[['Phi-3.5 / SimpleQA 暫定評価結果']];
summary.getRange('A2').format.font={...font,size:16};
summary.getRange('A3').values=[['2026年10月19日集計']];
summary.getRange('A3').format.font={...font,color:'#64687A',size:10};
summary.getRange('A4:F4').format.borders={bottom:{style:'thin',color:'#5C61F2'}};

records.getRange('A1:G2').format.font=font;
records.getRange('A1').values=[['採点記録（保存ログから抽出）']];
records.getRange('A2').values=[['出典：samples.jsonl / recovery_samples.jsonl']];
records.getRange('A3').values=[[`実行ID：${data.run_id}`]];
records.getRange('A4').values=[['A = CORRECT、B = INCORRECT、C = NOT_ATTEMPTED。各行は採点済みの1問。']];
records.getRange('A5:G5').values=[['問題番号','採点ラベル','Seed','生成トークン数','生成終了理由','採点出力','出典ファイル']];
const end=data.records.length+5;
records.getRange(`A6:G${end}`).values=data.records;
records.getRange(`A5:G${end}`).format.font={...font,size:10};
records.getRange(`A5:G${end}`).format.rowHeight=22;
records.getRange(`A5:G${end}`).format.verticalAlignment='center';
for(const [col,width] of [['A',14],['B',14],['C',17],['D',19],['E',19],['F',14],['G',34]]){
  records.getRange(`${col}5:${col}${end}`).format.columnWidth=width;
}
records.getRange(`A6:A${end}`).setNumberFormat('0');
records.getRange(`C6:C${end}`).setNumberFormat('0');
records.getRange(`D6:D${end}`).setNumberFormat('#,##0');
records.freezePanes.freezeRows(5);
records.tables.add(`A5:G${end}`,true,'SavedGrades');

function head(sheet,range){
  sheet.getRange(range).format={fill:'#343655',font:{...font,color:'#FFFFFF',bold:true},rowHeight:28,horizontalAlignment:'center'};
}
summary.getRange('A5:C5').values=[['採点結果','件数','構成比']];
summary.getRange('A6:A9').values=[['正解（CORRECT）'],['棄権（NOT_ATTEMPTED）'],['誤答（INCORRECT）'],['合計（採点済み）']];
summary.getRange('B6:B9').formulas=[
  [`=COUNTIFS('採点記録'!$B$6:$B$${end},"A")`],
  [`=COUNTIFS('採点記録'!$B$6:$B$${end},"C")`],
  [`=COUNTIFS('採点記録'!$B$6:$B$${end},"B")`],['=SUM(B6:B8)']];
summary.getRange('C6:C9').formulas=[['=B6/$B$9'],['=B7/$B$9'],['=B8/$B$9'],['=SUM(C6:C8)']];
summary.getRange('B6:B9').setNumberFormat('#,##0');
summary.getRange('C6:C9').setNumberFormat('0.00%');
summary.getRange('A9:C9').format.borders={top:{style:'thin',color:'#BEC1D0'}};
summary.getRange('A9:C9').format.font={...font,bold:true};

summary.getRange('A12:C12').values=[['評価指標','値','']];
summary.getRange('A13:A15').values=[['回答時正答率'],['回答率（正解＋誤答）'],['SimpleQA F-score']];
summary.getRange('B13:B15').formulas=[['=IF(B6+B8=0,"n.a.",B6/(B6+B8))'],['=(B6+B8)/B9'],['=2*B6/(B9+B6+B8)']];
summary.getRange('B13:B15').setNumberFormat('0.00%');
summary.getRange('A17').values=[['回答時正答率 = 正解 / (正解 + 誤答)']];
summary.getRange('A17').format.font={...font,size:10,color:'#64687A'};

summary.getRange('A20:C20').values=[['評価の進捗','件数','全体比']];
summary.getRange('A21:A25').values=[['全問題'],['採点済み'],['未採点'],['うち反復生成エラー'],['その他未採点']];
summary.getRange('B21').values=[[data.total]];
summary.getRange('B22:B23').formulas=[['=B9'],['=B21-B22']];
summary.getRange('B24').values=[[data.known_inference_errors]];
summary.getRange('B25').formulas=[['=B23-B24']];
summary.getRange('C21:C23').formulas=[['=B21/$B$21'],['=B22/$B$21'],['=B23/$B$21']];
summary.getRange('B21:B25').setNumberFormat('#,##0');
summary.getRange('C21:C23').setNumberFormat('0.00%');

summary.getRange('E5:F5').values=[['実験条件','設定']];
summary.getRange('E6:F13').values=[
  ['回答モデル',data.answer_model],['採点モデル',data.grader_model],
  ['回答 temperature',data.answer_temperature],['採点 temperature',data.grader_temperature],
  ['Seed（全問共通）',data.seed],['回答上限（tokens）',data.num_predict],
  ['回答プロンプト','質問文のみ'],['採点モデルの推論モード','think=False']];
summary.getRange('F8:F9').setNumberFormat('0.0');
summary.getRange('F10:F11').setNumberFormat('0');
summary.getRange('E15').values=[['出力上限に到達した回答（件）']];
summary.getRange('F15').formulas=[[`=COUNTIFS('採点記録'!$E$6:$E$${end},"length")`]];
summary.getRange('E16').values=[['採点済みに占める上限到達率']];
summary.getRange('F16').formulas=[['=F15/B9']];
summary.getRange('F16').setNumberFormat('0.00%');
summary.getRange('E19').values=[['集計上の注記']];
summary.getRange('E19').format.font={...font,bold:true};
summary.getRange('E20:E24').values=[
  ['構成比の分母は採点済み件数。'],['未採点は正解・誤答・棄権に含めない。'],
  ['Qwen3.5:4bによる自動採点。人手検証前。'],
  ['OpenAI公表値とは評価条件が異なる。'],['記録時点の暫定集計。全問の最終結果ではない。']];
summary.getRange('E26').values=[['最終採点応答（JST）']];
summary.getRange('F26').values=[[data.latest_response_jst.slice(0,19).replace('T',' ')]];
summary.getRange('F26').format.font={...font,size:10};
for(const r of ['A5:C5','A12:C12','A20:C20','E5:F5'])head(summary,r);
head(records,'A5:G5');

wb.recalculate();
const observed=summary.getRange('B6:B9').values.flat();
if(JSON.stringify(observed)!==JSON.stringify([data.counts.A,data.counts.C,data.counts.B,data.graded])){
  throw new Error(`Count mismatch: ${JSON.stringify(observed)}`);
}
if(Math.abs(summary.getRange('B13').values[0][0]-data.accuracy_given_attempted)>1e-10)throw new Error('Accuracy mismatch');
if(Math.abs(summary.getRange('B15').values[0][0]-data.f_score)>1e-10)throw new Error('F-score mismatch');
console.log((await wb.inspect({kind:'table',range:'集計!A5:C15',include:'values,formulas',tableMaxRows:11,tableMaxCols:3,maxChars:2500})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
for(const [name,range,file] of [['集計','A1:F28','summary_preview.png'],['採点記録','A1:G12','records_preview.png']]){
  const preview=await wb.render({sheetName:name,range,scale:1.4,format:'png'});
  await fs.writeFile(`${out}/support/${file}`,new Uint8Array(await preview.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);
await file.save(`${out}/simpleqa_interim_20261019.xlsx`);
console.log(`Exported ${out}/simpleqa_interim_20261019.xlsx`);
