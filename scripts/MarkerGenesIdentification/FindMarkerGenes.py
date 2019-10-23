import sys
import numpy as np
import os
from OnClassPred import OnClassPred

from utils import *

output_dir = '../../OnClass_data/marker_gene/'
if not os.path.exists(output_dir):
	os.makedirs(output_dir)
## read data
data_file = '../../OnClass_data/raw_data/tabula-muris-senis-facs'

if not os.path.isfile(output_dir + 'FACS-predicted_score_matrix.npy'):
	train_X, train_Y_str, genes_list = read_data(filename=data_file, return_genes=True)
	tms_genes_list = [x.upper() for x in list(genes_list.values())[0]]
	ntrain,ngene = np.shape(train_X)
	## embedd the cell ontology
	unseen_l, l2i, i2l, onto_net, Y_emb, cls2cls = ParseCLOnto(train_Y_str, co_dim = 200, co_mi = 0)
	train_Y = MapLabel2CL(train_Y_str, l2i)

	## train and predict
	OnClass_obj = OnClassPred()
	OnClass_obj.train(train_X, train_Y, Y_emb, max_iter=20, nhidden=[100])
	test_Y_pred = OnClass_obj.predict(test_X)

	np.save(output_dir + 'FACS-predicted_score_matrix.npy', test_Y_pred)

fig_dir = '../../OnClass_data/figures/marker_gene/'
if not os.path.exists(fig_dir):
	os.makedirs(fig_dir)

data_file = '../../OnClass_data/raw_data/tabula-muris-senis-facs'
train_X, train_Y_str, genes_list = read_data(filename=data_file, return_genes=True)
train_X = np.log1p(train_X.todense()+1)
tms_genes_list = [x.upper() for x in list(genes_list.values())[0]]
unseen_l, l2i, i2l, onto_net, Y_emb, cls2cls = ParseCLOnto(train_Y_str)
train_Y = MapLabel2CL(train_Y_str, l2i)
genes = genes_list[datanames[0]]
g2i = {}
i2g = {}
for i,g in enumerate(genes):
	g2i[g.lower()] = i
	i2g[i] = g
ngene = len(genes)

test_Y_pred = np.load(output_dir + 'FACS-predicted_score_matrix.npy')

ncell = np.shape(test_Y_pred)[0]
co2name, name2co = get_ontology_name()
tp2genes = read_type2genes(g2i)
thres = np.array(range(1,1000))
topk = 50
in_tms_ranks = []
not_tms_ranks = []
n_in_tms =0
for tp in tp2genes:
	ci = l2i[tp]
	k_bot_cells = np.argsort(test_Y_pred[:,ci])[:topk]
	k_top_cells = np.argsort(test_Y_pred[:,ci])[ncell-topk:]
	pv = scipy.stats.ttest_ind(train_X[k_top_cells,:], train_X[k_bot_cells,:], axis=0)[1]
	top_mean = np.mean(train_X[k_top_cells,:],axis=0)
	bot_mean = np.mean(train_X[k_bot_cells,:],axis=0)
	for g in range(ngene):
		if top_mean[0,g] < bot_mean[0,g]:
			pv[g] = 1.
	pv_sort = list(np.argsort(pv))
	min_rank = 1000000
	for g in tp2genes[tp]:
		gid = g2i[g.lower()]
		rank = pv_sort.index(gid)
		min_rank = min(rank, min_rank)
	if ci in np.unique(train_Y):
		in_tms_ranks.append(min_rank)
	else:
		not_tms_ranks.append(min_rank)

not_tms_ranks = np.array(not_tms_ranks)
in_tms_ranks = np.array(in_tms_ranks)


in_tms_y = []
not_tms_y = []
for t in thres:
	in_tms_y.append( len(np.where(in_tms_ranks <= t)[0]) / len(in_tms_ranks))
	not_tms_y.append( len(np.where(not_tms_ranks <= t)[0]) / len(not_tms_ranks))


fig = plt.figure()
ax = fig.add_subplot(1,1,1)
plt.plot(thres, in_tms_y, 'g', label='Seen cell types (n=%d)'%len(in_tms_ranks), linewidth=2)
plt.plot(thres, not_tms_y, 'y', label='Unseen cell types (n=%d)'%len(not_tms_ranks), linewidth=2)
plt.legend(loc="lower right",frameon=False)

plt.ylabel('Percentage of cell types')
plt.xlabel('Rank of marker genes')
#ax.yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))
vals = ax.get_yticks()
ax.set_yticklabels(['{:,.0%}'.format(x) for x in vals])
plt.tight_layout()
plt.savefig(fig_dir+'mark_genes.pdf')


fmarker_genes = open(output_dir+'marker_genes.txt','w')
for ci in range(nlabel):
	tp = i2l[ci]
	k_bot_cells = np.argsort(test_Y_pred[:,ci])[:topk]
	k_top_cells = np.argsort(test_Y_pred[:,ci])[ncell-topk:]
	pv = scipy.stats.ttest_ind(train_X[k_top_cells,:], train_X[k_bot_cells,:], axis=0)[1]
	top_mean = np.mean(train_X[k_top_cells,:],axis=0)
	bot_mean = np.mean(train_X[k_bot_cells,:],axis=0)
	for g in range(ngene):
		if top_mean[0,g] < bot_mean[0,g]:
			pv[g] = 1.
	pv_sort = list(np.argsort(pv))
	min_rank = 1000000
	fmarker_genes.write(tp+'\t')
	for i in range(100):
		fmarker_genes.write(i2g[pv_sort[i]]+'\t')
	fmarker_genes.write('\n')
fmarker_genes.close()