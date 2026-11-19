import csv,json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def rows(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
out={}
for p in sorted(root.glob('outputs/experiment_*')):
    cfg=json.loads((p/'config/config.json').read_text())
    files=list(p.rglob('*'))
    out[p.name]={'profile':cfg['profile'],'seeds':cfg['run']['seeds'],'folds':cfg['run']['n_folds'],'final_report':(p/'reports/final_experiment_report.md').exists(),'metrics_rows':len(rows(p/'metrics/recording_metrics.csv')) if (p/'metrics/recording_metrics.csv').exists() else 0}
p=root/'outputs/experiment_20261116_143634'
manifest=rows(p/'config/dataset_manifest.csv')
dups={}
for r in manifest:dups.setdefault(r['sha1'],[]).append(r['rec_id'])
dups=[v for v in dups.values() if len(v)>1]
assign=rows(p/'config/fold_assignments.csv'); crossed=[]
for seed in sorted(set(r['seed'] for r in assign)):
 for fold in sorted(set(r['fold'] for r in assign)):
  for group in dups:
   roles={r['role'] for r in assign if r['seed']==seed and r['fold']==fold and r['rec_id'] in group}
   if len(roles)>1:crossed.append({'seed':seed,'fold':fold,'roles':sorted(roles)})
out['duplicate_audit']={'groups':dups,'cross_partition_splits':crossed,'count':len(crossed)}
out['main_recording_metrics']=rows(p/'metrics/recording_metrics.csv')
out['main_paired']=rows(p/'metrics/paired_model_comparisons.csv')
out['parameters']=json.loads((p/'config/model_parameter_counts.json').read_text())
train=rows(p/'metrics/training_summary.csv')
out['head_parameter_observations']={m:sorted(set(r['n_params'] for r in train if r['model']==m and not r['tag'].startswith('loao'))) for m in ['E4','E5','E7','E8','E9','E11']}
out['fit_seconds']={m:sum(float(r['seconds']) for r in train if r['model']==m and not r['tag'].startswith('loao'))/len([r for r in train if r['model']==m and not r['tag'].startswith('loao')]) for m in ['E4','E5','E7','E8','E9','E11']}
a=root/'outputs_gwst_vqc_ablation/without_augmentation/experiment_20261117_100749'
b=root/'outputs_gwst_vqc_ablation/with_mixup_augmentation/experiment_20261117_101255'
out['quick_equal_files']={str(f.relative_to(a)):hashlib.sha256(f.read_bytes()).hexdigest()==hashlib.sha256((b/f.relative_to(a)).read_bytes()).hexdigest() for f in a.rglob('*.csv') if (b/f.relative_to(a)).exists() and ('metrics' in f.parts or 'predictions' in f.parts)}
out['main_vs_later_baseline_equal']={str(f.relative_to(p)):(root/'outputs/experiment_20261116_202913'/f.relative_to(p)).exists() and f.read_bytes()==(root/'outputs/experiment_20261116_202913'/f.relative_to(p)).read_bytes() for f in (p/'metrics').glob('*.csv')}
(root/'report_work/audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ['main_recording_metrics','main_paired']},indent=2))
import fitz
for file in root.glob('*.pdf'):
 doc=fitz.open(file)
 text='\n'.join(page.get_text() for page in doc)
 (root/'report_work'/(file.stem+'.txt')).write_text(text,encoding='utf-8')
 print('\nPAPER',file.name,'PAGES',len(doc),'\n',text[:1700])
