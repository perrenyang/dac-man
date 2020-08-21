#!/usr/bin/env python3
# TODO: check above?
import sys

import dacman
from dacman.compare import base
from dacman.compare.adaptor import DacmanRecord

import json
from jsonschema import validate

class IdaesVisAdaptor(base.DacmanRecordAdaptor):

    def transform(self, data_path):
        headers = []
        with open(data_path) as f:
            data = json.load(f)
        return headers, data

class IdaesVisPlugin(base.Comparator):

    @staticmethod
    def description():
        return "A Dacman plug-in to compare serialized IDAES models produced by the visualizer"

    @staticmethod
    def supports():
        return ['idaesvis']

    def get_record(self, path):
        ext = 'idaesvis'
        rec = DacmanRecord(path)
        rec.file_support = {ext: True}
        rec.lib_support = {ext: 'json'}  # TODO ...?
        rec.file_adaptors = {ext: IdaesVisAdaptor}
        rec._transform_source()  # TODO this seems mildly questionable?
        return rec

    def compare(self, path_a, path_b, *args):
        rec_a = self.get_record(path_a)
        rec_b = self.get_record(path_b)
        # print(f'type: {type(rec_a.data)}; tostring: {str(type(rec_a.data))}')
        # print(str(rec_a.data))
        # TODO pycharm complains 'cos this attribute isn't in an init; complaint seems valid...?
        try:
            self.metrics = self.get_model_change_metrics(rec_a, rec_b)
        except Exception as e:
            self.metrics = {'error': str(e)}

        return self.metrics

    def percent_change(self):
        frac = self.metrics.get('frac_changed', 0)
        return frac * 100

    # TODO this seems fine as a static? for that matter, most of the class seems static?
    def stats(self, changes):
        print(changes)

    @staticmethod
    # Taken from IDAES ui.flowsheet_comparer
    def _compare_models(existing_model, new_model):
        """
           Compares two models that are in this format

           .. code-block:: json

               {
                   "model": {
                       "id": "id",
                       "unit_models": {
                           "M101": {
                               "image": "mixer.svg",
                               "type": "mixer"
                           }
                       },
                       "arcs": {
                           "s03": {
                               "source": "M101",
                               "dest": "H101",
                               "label": "molar flow ('Vap', 'hydrogen') 0.5"
                           }
                       }
                   },
                   "cells": [{ "--jointjs code--": "--jointjs code--" }]
               }

           :param existing_model: The current model to compare against
           :param new_model: The new model that has changes
           :return: A diff between the models in this format:

           .. code-block:: json

               {
                   "M111": {
                       "type": "flash",
                       "image": "flash.svg",
                       "action": "1",
                       "class": "unit model"
                   },
                   "s03": {
                       "source": "M101",
                       "dest": "F102",
                       "label": "Hello World",
                       "action": "3",
                       "class": "arc"
                   },
                   "s11": {
                       "source": "H101",
                       "dest": "F102",
                       "label": "molar flow ('Vap', 'hydrogen') 0.5",
                       "action": "2",
                       "class": "arc"
                   }
               }

           """
        _REMOVE = 0
        _ADD = 1
        _CHANGE = 2

        diff_model = {}
        model_schema = {
            "type": "object",
            "properties": {
                "id": {"type": ["number", "string"]},
                "unit_models": {
                    "type": "object",
                },
                "arcs": {
                    "type": "object",
                }
            },
            "required": ["id", "unit_models", "arcs"]
        }

        # Copy the new model into the out_json's model key

        out_json = dict(existing_model)
        try:
            out_json["model"] = new_model["model"]
        except KeyError as error:
            msg = "Unable to find 'model' section of new model json"
            raise KeyError(msg)

        validate(instance=existing_model["model"], schema=model_schema)
        validate(instance=new_model["model"], schema=model_schema)

        try:
            existing_model = existing_model["model"]
        except KeyError as error:
            msg = "Unable to find 'model' section of existing model json"
            raise KeyError(msg)
        # If the existing model is empty then return an empty diff_model
        # and the full json from the new model
        if existing_model["unit_models"] == {} and \
                existing_model["arcs"] == {}:
            return {}, new_model

        # If the models are the same return an empty diff_model and the full json from
        # the new model. This will happen when the user moves something in the
        # graph but doesn't change the actual idaes model
        if existing_model == new_model["model"]:
            return {}, new_model

        try:
            new_model = new_model["model"]
        except KeyError as error:
            msg = "Unable to find 'model' section of new model json"
            raise KeyError(msg)

        unit_model_schema = {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "image": {"type": "string"}
            },
        }

        # Check for new or changed unit models
        for item, value in new_model["unit_models"].items():
            validate(instance=value, schema=unit_model_schema)
            if item not in existing_model["unit_models"]:
                diff_model[item] = value
                diff_model[item]["action"] = _ADD
                diff_model[item]["class"] = "unit model"
            elif existing_model["unit_models"][item] != value:
                diff_model[item] = value
                diff_model[item]["action"] = _CHANGE
                diff_model[item]["class"] = "unit model"
            elif existing_model["unit_models"][item] == value:
                pass
            else:
                msg = ("Unknown diff between new model and existing_model. "
                       "Key: " + str(item) + " new model value: " + str(value) + ", "
                        "existing model value: " + str(existing_model["unit_models"][item]))
                raise UnknownModelDiffException(msg)

        # Check for unit models that have been removed
        for item, value in existing_model["unit_models"].items():
            validate(instance=value, schema=unit_model_schema)
            if item not in new_model["unit_models"]:
                diff_model[item] = value
                diff_model[item]["action"] = _REMOVE
                diff_model[item]["class"] = "unit model"

        arc_schema = {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "dest": {"type": "string"},
                "label": {"type": "string"}
            }
        }

        # Check for new or changed arcs
        for item, value in new_model["arcs"].items():
            validate(instance=value, schema=arc_schema)
            if item not in existing_model["arcs"]:
                diff_model[item] = value
                diff_model[item]["action"] = _ADD
                diff_model[item]["class"] = "arc"
            elif existing_model["arcs"][item] != value:
                diff_model[item] = value
                diff_model[item]["action"] = _CHANGE
                diff_model[item]["class"] = "arc"
            else:
                pass

        # Check for arcs that have been removed
        for item, value in existing_model["arcs"].items():
            validate(instance=value, schema=arc_schema)
            if item not in new_model["arcs"]:
                diff_model[item] = value
                diff_model[item]["action"] = _REMOVE
                diff_model[item]["class"] = "arc"

        return diff_model, out_json

    def get_model_change_metrics(self, rec_a, rec_b):
        # TODO: what's the best way to use these across both functions, one of which is static?
        #  These are basically static values for the class as a whole.
        _REMOVE = 0
        _ADD = 1
        _CHANGE = 2
        change_matrix = {'arc': [0, 0, 0], 'unit model': [0, 0, 0]}

        m1 = rec_a.data
        m2 = rec_b.data
        changes, _ = self._compare_models(m1, m2)
        for item_info in changes.values():
            itemtype = item_info['class']
            modification = item_info['action']
            change_matrix[itemtype][modification] += 1

        frac_changed = 0.5  # TODO

        return {
            'removed arcs': change_matrix['arc'][_REMOVE],
            'added arcs': change_matrix['arc'][_ADD],
            'modified arcs': change_matrix['arc'][_CHANGE],
            'removed unit models': change_matrix['unit model'][_REMOVE],
            'added unit models': change_matrix['unit model'][_ADD],
            'modified unit models': change_matrix['unit model'][_CHANGE],
            'frac_changed': frac_changed,
            # TODO are any of these arbitrary and user-defined?
            # 'sum(A - B)': sum_of_delta,
            # 'mean(A - B)': mean_of_delta,
            # 'norm(A - B)': norm_of_delta,
            # 'delta(max(A) - max(B))': delta_max,
            # 'delta(min(A) - min(B))': delta_min,
        }




def run_idaes_vis(path_a, path_b):
    comparisons = [(path_a, path_b)]
    differ = dacman.DataDiffer(comparisons, dacman.Executor.DEFAULT)
    differ.use_plugin(IdaesVisPlugin)
    differ.start()

if __name__ == '__main__':
    cli_args = sys.argv[1:]
    path_a, path_b = cli_args[0], cli_args[1]
    run_idaes_vis(path_a, path_b)