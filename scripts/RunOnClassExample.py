import sys
from scipy import stats, sparse
import numpy as np
import os
from collections import Counter
from OnClass.OnClassModel import OnClassModel
from OnClass.utils import *

data_dir = '../OnClass_data/'
scrna_data_dir = '/oak/stanford/groups/rbaltman/swang91/Sheng_repo/data/SingleCell/'
feature_file1 = scrna_data_dir + 'TMS_official_060520/tabula-muris-senis-droplet-official-raw-obj.h5ad'
feature_file2 = scrna_data_dir + 'TMS_official_060520/tabula-muris-senis-facs-official-raw-obj.h5ad'
label_key1 = 'cell_ontology_class'
label_key2 = 'cell_ontology_class'

cell_type_nlp_emb_file, cell_type_network_file, cl_obo_file = read_ontology_file('muris', data_dir)
OnClass = OnClassModel(cell_type_nlp_emb_file = cell_type_nlp_emb_file, cell_type_network_file = cell_type_network_file)



feature1, genes1, label1, _, _ = read_data(feature_file1, cell_ontology_ids = OnClass.cell_ontology_ids,
	exclude_non_leaf_ontology = False, tissue_key = 'tissue', AnnData_label_key=label_key1,filter_key = {},
	nlp_mapping = False, cl_obo_file = cl_obo_file, cell_ontology_file = cell_type_network_file, co2emb = OnClass.co2vec_nlp)

feature2, genes2, label2, _, _ = read_data(feature_file2, cell_ontology_ids = OnClass.cell_ontology_ids,
exclude_non_leaf_ontology = False, tissue_key = 'tissue', filter_key = {}, AnnData_label_key=label_key2,
nlp_mapping = False, cl_obo_file = cl_obo_file, cell_ontology_file = cell_type_network_file, co2emb = OnClass.co2vec_nlp)


common_genes = np.array(list(set(genes1) & set(genes2)))
gid1 = find_gene_ind(genes1, common_genes)
gid2 = find_gene_ind(genes2, common_genes)

train_X = feature1[:1000, gid1]
test_X = feature2[:2000, gid2]
train_Y_str = label1[:1000] #put a text label here, it could either be cell type name or cell ontology id. OnClass will map it automatically
test_Y_str = label2[:2000]

print (np.shape(train_X),np.shape(test_X))

co2emb, co2i, i2co, ontology_mat = OnClass.EmbedCellTypes(train_Y_str)
train_X, test_X = OnClass.align_train_test_expression(train_X, test_X)
print ('train start')

OnClass.BuildModel(OnClass.co2emb, ngene = np.shape(train_X)[1])
OnClass.Train(train_X, train_Y_str)

#use_normalize=False will return a tree-based prediction, where parent node often has higher score than child node. use_normalize=True will normalize among child nodes and parent nodes
pred_Y_seen, pred_Y_all, pred_label = OnClass.Predict(test_X, use_normalize=True)
print (Counter(pred_label))
pred_Y_seen, pred_Y_all, pred_label = OnClass.Predict(test_X, use_normalize=False)
print (Counter(pred_label))