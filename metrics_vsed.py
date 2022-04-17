# coding=utf-8
# Copyright 2020 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datasets

# TODO: Add BibTeX citation
_CITATION = """\
@InProceedings{huggingface:metric,
title = {A great new metric},
authors={huggingface, Inc.},
year={2020}
}
"""

_DESCRIPTION = """\
This a metric for the paper "Data Augmentation for Rare Symptoms in Vaccine Side-Effect Detection" (BioNLP 2022)
We evaluate on three test sets: Full, CUI-mapped, and Long-tail
"""

_KWARGS_DESCRIPTION = """
To be updated
"""

@datasets.utils.file_utils.add_start_docstrings(_DESCRIPTION, _KWARGS_DESCRIPTION)
class VSEDMetric(datasets.Metric):
    """ Metric for precision, recall and F1 on three test sets: Full, CUI-mapped, and Long-tail"""

    def _info(self):
        # TODO: Specifies the datasets.MetricInfo object
        return datasets.MetricInfo(
            # This is the description that will appear on the metrics page.
            description=_DESCRIPTION,
            citation=_CITATION,
            inputs_description=_KWARGS_DESCRIPTION,
            # This defines the format of each prediction and reference
            features=datasets.Features({
                'predictions': datasets.Value('string'),
                'references': {
                        "vid": datasets.Value("int32"),
                        "symptoms": datasets.features.Sequence(datasets.Value('string')),
                }
            }),
            # Additional links to the codebase or references
            codebase_urls=["https://github.com/huggingface/datasets/blob/master/templates/new_metric_script.py"],
            # To be updated
            # reference_urls=["http://path.to.reference.url/new_metric"] 
        )

    def _download_and_prepare(self, dl_manager):
        self.norm2ori = {}  # normalized symptom name to original symtpom name

        # Full entity set test
        symptomfile = "data/symptoms.tsv"
        self.symptoms = set()     
        for i, w in enumerate(open(symptomfile, "r")):
            if i == 0:
                continue
            _, sym, ori, _ = w.split("\t")
            self.symptoms.add(sym)
            self.norm2ori[sym] = ori

        # CUI-mapped entity set
        cuifile = "data/symptoms_cui.tsv"
        self.symptoms_cui = set()
        for i, w in enumerate(open(cuifile, "r")):
            if i == 0:
                continue
            tokens = w.strip().split("\t")
            if len(tokens) > 3:
                _, sym_ori, symnorm, _, _ = w.split("\t")
                self.symptoms_cui.add(symnorm)
        
        # long-tail entity set
        longtailfile = "data/symptoms_longtail.tsv"
        self.symptoms_longtail = set()
        for i, w in enumerate(open(longtailfile, "r")):
            if i == 0:
                continue
            _, sym, ori, _ = w.split("\t")
            self.symptoms_longtail.add(sym)

    def _compute(self, predictions, references):
        """Returns the scores"""
        test_type = ["full", "cui", "longtail"]
        target_symp_set = {
            "full": self.symptoms,
            "cui": self.symptoms_cui,
            "longtail": self.symptoms_longtail
        }

        results = {}
        for tt in test_type:
            results[tt] = {
                "global_tp": 0,
                "global_n_true": 0,
                "global_n_pos": 0,
                "macro_p": 0,
                "macro_r": 0,
                "n_target_doc": 0, # for a denominator of macro metrics 
            }

        for pred, ref in zip(predictions, references):
            for tt in test_type:
                # the number of gold entities
                gold_entities = ref["symptoms"]
                local_gold_ent = []
                for ge in gold_entities:
                    if ge in target_symp_set[tt]:
                        local_gold_ent.append(ge)
                
                if len(local_gold_ent) > 0:
                    local_n_true = len(local_gold_ent)  # the number of gold entities per each example
                    results[tt]["global_n_true"] += local_n_true
                    results[tt]["n_target_doc"] += 1

                    # get entities from generated texts
                    model_outputs = [x.strip().lower().replace(" ", "") for x in pred.strip().split(",")]
                    pred_symps = []
                    for mo in model_outputs:
                        if mo in target_symp_set[tt]:
                            pred_symps.append(mo)

                    local_n_pos = len(pred_symps)
                    results[tt]["global_n_pos"] += local_n_pos

                    local_tp = 0
                    for candi in local_gold_ent:
                        if pred.find(candi) != -1:  # true positive
                            local_tp += 1
                            results[tt]["global_tp"] += 1

                    cur_p = (local_tp / local_n_pos) if local_n_pos != 0 else 0
                    cur_r = (local_tp / local_n_true) if local_n_true != 0 else 0

                    results[tt]["macro_p"] += cur_p
                    results[tt]["macro_r"] += cur_r

        assert len(predictions) == results["full"]["n_target_doc"]

        for tt in test_type:
            # for macro
            results[tt]["macro_precision"] = results[tt]["macro_p"]/results[tt]["n_target_doc"] if results[tt]["n_target_doc"] > 0 else 0
            results[tt]["macro_recall"] = results[tt]["macro_r"]/results[tt]["n_target_doc"] if results[tt]["n_target_doc"] > 0 else 0

            # for micro
            results[tt]["micro_precision"] = results[tt]["global_tp"]/results[tt]["global_n_pos"] if results[tt]["global_n_pos"] > 0 else 0
            results[tt]["micro_recall"] = results[tt]["global_tp"]/results[tt]["global_n_true"] if results[tt]["global_n_true"] > 0 else 0

            # for F1 scores
            results[tt]["macro_f1"] = 2*results[tt]["macro_precision"]*results[tt]["macro_recall"]/(results[tt]["macro_precision"]+results[tt]["macro_recall"]) if results[tt]["macro_precision"]+results[tt]["macro_recall"] != 0 else 0
            results[tt]["micro_f1"] = 2*results[tt]["micro_precision"]*results[tt]["micro_recall"]/(results[tt]["micro_precision"]+results[tt]["micro_recall"]) if results[tt]["micro_precision"]+results[tt]["micro_recall"] != 0 else 0

        return results