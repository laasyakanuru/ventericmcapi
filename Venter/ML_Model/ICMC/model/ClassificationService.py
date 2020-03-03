import os

import numpy as np
import pandas as pd
from django.conf import settings

from .ImportGraph import ImportGraph
from Venter.models import Category


class ClassificationService:
    def __init__(self):
        model_category_list = Category.objects.filter(organisation_name='ICMC').values_list('category', flat=True)
        category_set = set(model_category_list)
        database_category_list = list(category_set)
        database_category_list.sort()
        self.index_complaint_title_map = {}
        self.index_complaint_title_map = dict(list(enumerate(database_category_list)))

        self.g0 = ImportGraph.get_instance()

    def get_probs_graph(self, model_id, data, flag):
        if model_id == 0:
            model = self.g0

        data = model.process_query(data, flag)
        # print('DATA SHAPE', data.shape)
        return model.run(data)

    def get_top_3_cats_with_prob(self, data):
        prob1 = self.get_probs_graph(0, data, flag=1)

        result_list = []
        for x in range(prob1.shape[0]):
            final_prob = prob1[x]
            final_sorted = np.argsort(final_prob)

            final_categories = []
            final_probabilities = []

            for i in range(3):
                final_categories.append(self.index_complaint_title_map[final_sorted[-3:][2-i]])
                final_probabilities.append(int(float(final_prob[final_sorted[-3:][2-i]])*100))
            result = {}
            for c, p in zip(final_categories, final_probabilities):
                result[c] = p
            result_list.append(result)
	

        return result_list
