"""Draw figures from archived CSVs only; never imports or fits pipeline models."""
import os,csv,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'.venv/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch,Rectangle

OUT=ROOT/'report_work/revision_figures';OUT.mkdir(exist_ok=True)
def read(path):return list(csv.DictReader(open(path,encoding='utf-8-sig')))
M={r['model']:r for r in read(ROOT/'outputs/experiment_20261116_143634/metrics/recording_metrics.csv')}
L={r['model']:r for r in read(ROOT/'outputs/experiment_20261116_202913/metrics/recording_metrics.csv')}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
COL=['#395E7A','#6A91A9','#A26D45','#859C75','#B4A17D']
MET=['accuracy','balanced_accuracy','sensitivity','specificity','macro_f1']; LABEL=['Accuracy','Balanced','Sensitivity','Specificity','Macro F1']
def panels(keys,names,name,cols=2):
 rows=math.ceil(len(keys)/cols)
 fig,axes=plt.subplots(rows,cols,figsize=(7.2,2.0*rows),squeeze=False,layout='constrained')
 for ax,k,title in zip(axes.flat,keys,names):
  vals=[float(M[k][v])*100 for v in MET]
  ax.barh(range(5),vals,color=COL,height=.65)
  ax.set_yticks(range(5),LABEL,fontsize=8.5);ax.invert_yaxis();ax.set_xlim(0,112)
  ax.set_xticks([0,25,50,75,100]);ax.tick_params(axis='x',labelsize=8);ax.set_title(title,loc='left',fontweight='bold',fontsize=10)
  ax.set_axisbelow(True);ax.grid(axis='x',alpha=.15)
  for i,v in enumerate(vals):ax.text(v+1,i,f'{v:.2f}',va='center',fontsize=8)
 for ax in list(axes.flat)[len(keys):]:ax.axis('off')
 fig.savefig(OUT/name,dpi=230);plt.close(fig)
panels(['E1','E2','E3'],['E1 Random forest','E2 SVM','E3 MI selected RF'],'handcrafted_metrics.png',1)
panels(['E4','E5','E6','E7','E12T'],['E4 Linear','E5 MLP','E6 RBF SVM','E7 VQC','E12T No CNOT'],'transformer_metrics.png')
panels(['E8','E9','E10','E11','E12B'],['E8 Linear','E9 MLP','E10 RBF SVM','E11 VQC','E12B No CNOT'],'bilstm_metrics.png')
panels(['FT-T-lin','FT-T-mlp','FT-T-vqc','FT-B-lin','FT-B-mlp','FT-B-vqc'],['Transformer linear','Transformer MLP','Transformer VQC','Bi LSTM linear','Bi LSTM MLP','Bi LSTM VQC'],'finetuned_metrics.png')

keys=[k for k in L if not k.startswith('AUG_')]
fig,ax=plt.subplots(figsize=(7.2,6.2),layout='constrained');y=list(range(len(keys)))
ax.barh([v-.18 for v in y],[100*float(L[k]['balanced_accuracy']) for k in keys],height=.33,label='Baseline in same archive',color=COL[0])
ax.barh([v+.18 for v in y],[100*float(L['AUG_'+k]['balanced_accuracy']) for k in keys],height=.33,label='Waveform augmentation',color=COL[2])
ax.set_yticks(y,keys,fontsize=8);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Recording balanced accuracy (%)')
ax.legend(loc='lower right',fontsize=8);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.savefig(OUT/'augmentation_all.png',dpi=230);plt.close(fig)

fig,(a,b)=plt.subplots(1,2,figsize=(7.2,2.5),layout='constrained',sharey=True)
a.barh(['RF hold out','LSTM hold out','LSTM ten fold'],[90.74,87.04,74.44],color=COL[1]);a.set_title('Published wearable protocols',fontsize=10)
b.barh(['RF E1','Transformer MLP','Transformer VQC'],[100*float(M[k]['accuracy']) for k in ['E1','E5','E7']],color=[COL[0],COL[0],COL[2]]);b.set_title('Current recording grouped CV',fontsize=10)
# Independent categorical y labels are required for each study group.
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(7.2,2.5),layout='constrained')
for ax,labels,vals,title,col in [(axes[0],['RF hold out','LSTM hold out','LSTM ten fold'],[90.74,87.04,74.44],'Published wearable protocols',COL[1]),(axes[1],['RF E1','T MLP E5','T VQC E7'],[100*float(M[k]['accuracy']) for k in ['E1','E5','E7']],'Current recording grouped CV',COL[0])]:
 ax.barh(labels,vals,color=col);ax.invert_yaxis();ax.set_xlim(0,105);ax.tick_params(axis='y',labelsize=8.5);ax.set_title(title,fontsize=10);ax.set_xlabel('Accuracy (%)')
 for i,v in enumerate(vals):ax.text(v+1,i,f'{v:.2f}',va='center',fontsize=9)
fig.savefig(OUT/'base_comparison.png',dpi=230);plt.close(fig)

def diagram(name,items,figsize=(7.2,3.5)):
 fig,ax=plt.subplots(figsize=figsize,layout='constrained');ax.set_xlim(0,10);ax.set_ylim(0,len(items));ax.axis('off')
 for i,(title,detail) in enumerate(items):
  y=len(items)-i-.85
  ax.add_patch(Rectangle((.4,y),9.2,.67,facecolor='#E9EFF3',edgecolor='#7893A5',lw=.8))
  ax.text(5,y+.43,title,ha='center',va='center',fontsize=10,fontweight='bold')
  ax.text(5,y+.18,detail,ha='center',va='center',fontsize=8.5)
  if i<len(items)-1:ax.annotate('',xy=(5,y-.3),xytext=(5,y-.02),arrowprops=dict(arrowstyle='->',color='#395E7A'))
 fig.savefig(OUT/name,dpi=220);plt.close(fig)
diagram('pipeline.png',[
 ('Dataset audit and grouped partitions','90 files | 60 healthy and 30 epilepsy labelled | participant IDs unavailable'),
 ('WOSG and five second segmentation','Wavelet approximation filtering | 4 complete windows per recording'),
 ('GWST magnitude representation','225 frequency voices from 0.5 to 50 Hz | 2560 samples per window'),
 ('Two representation branches','450 L1 and entropy values  OR  64 temporal tokens by 225 frequencies'),
 ('Classical baselines or temporal encoding','RF / SVM / MI RF  OR  Transformer / Bi LSTM to a 6 value embedding'),
 ('Matched heads and separate fine tuning','Linear / MLP / RBF SVM / VQC / no CNOT control'),
 ('Recording aggregation and evaluation','Mean window probability | validation threshold | paired statistics')],(7.2,5.4))
diagram('transformer.png',[
 ('Token projection','[64,225] to [64,32] with sinusoidal position encoding'),
 ('Two pre normalised Transformer blocks','LayerNorm > 4 head self attention > residual; LayerNorm > FF 32-64-32 > residual'),
 ('Final normalisation and attention pooling','[64,32] to [32] | dropout 0.2 | GELU feedforward activation'),
 ('Shared bounded embedding','LayerNorm 32 > Linear 32 to 6 > tanh > matched head')],(7.2,3.3))
diagram('bilstm.png',[
 ('Token projection','[64,225] to [64,32]'),
 ('One bidirectional recurrent layer','16 forward and 16 backward hidden values concatenate at each token'),
 ('Dropout and attention pooling','[64,32] to [32] | dropout 0.2'),
 ('Shared bounded embedding','LayerNorm 32 > Linear 32 to 6 > tanh > matched head')],(7.2,3.3))
diagram('vqc.png',[
 ('Input calibration and state preparation','z in R6 > tanh(scale * z + bias) > RY(pi * value) on 6 qubits'),
 ('Three variational layers','Each layer: RY and RZ on each qubit, then CNOT ring 0>1>2>3>4>5>0'),
 ('Measurement and classical readout','6 Pauli Z expectations > Linear 6 to 1 > sigmoid | 55 total head parameters')],(7.2,2.5))
print('Created',len(list(OUT.glob('*.png'))),'figures from saved metrics and configuration.')
