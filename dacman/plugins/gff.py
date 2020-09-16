#!/usr/bin/env python3
import sys

import dacman
from dacman.compare import base
from dacman.compare.adaptor import DacmanRecord
import logging

# import gffutils

logger = logging.getLogger(__name__)

class GffPluginAdaptor(base.DacmanRecordAdaptor):
    def transform(self, data_path):
        headers = []
        data = []
        with open(data_path) as f:  # TODO??
            for line in f:
                # headers: lines starting with ## are directives, # are comments and probably should be ignored
                # unclear if ## can show up outside of the header
                if line.startswith('##'):
                    headers.append(line[2:])
                    continue

                if line.startswith('#'):
                    continue

                # transform to an array for dacman record.
                # ??? TODO ???
                # ['seqid', 'source', 'type', 'start', 'end', 'score', 'strand', 'phase', 'attributes']

                # we can serialize all of the features by alphebetically listing them
                # but how to preserve the hierarchical information?
                # - using the sqlite tables produced by gffutils seems like it would be bypassing the concept of Dacman Records
                # - using the gff structure results in stacking all of the annotation information into... strings?
                #     - maybe those parts can be further parsed I guess. Seems to result in duplicating the effort of gffutils, to the point
                #       that we may as well just be manually parsing though?

                feature_entry = line.split('\t')

                attrib_full_text = feature_entry[-1] # annotations are in the last (ninth) column
                attribs = {}
                for attrib_text in attrib_full_text.split(';'):
                    attrib_pair = attrib_text.split('=')
                    attribs[attrib_pair[0]] = attrib_pair[1]

                try:
                    data.append(attribs['ID'])  # TODO -- expand this when the time comes
                except KeyError as e:
                    logger.error(f'ID field not found! Original line:\n{line}')
                    logger.log(e)

        return headers, sorted(data)


class GffPlugin(base.Comparator):

    @staticmethod
    def description():
        return "A Dacman plug-in to compare GFF annotation files produced by genome analysis workflows."

    @staticmethod
    def supports():
        return ['gff']

    def get_record(self, path):
        ext = 'gff'
        rec = DacmanRecord(path)
        rec.file_support = {ext: True}
        rec.lib_support = {'gffutils'}
        rec.file_adaptors = {ext: GffPluginAdaptor}
        rec._transform_source()
        return rec

    def compare(self, path_a, path_b, *args):
        rec_a = self.get_record(path_a)
        rec_b = self.get_record(path_b)
        try:
            self.metrics = self.get_gff_change_metrics(rec_a, rec_b)
        except Exception as e:
            self.metrics = {'error': str(e)}
        return self.metrics

    def percent_change(self):
        frac = self.metrics.get('frac_changes', 0)
        return frac * 100

    def stats(self, changes):
        print(changes)

    def get_gff_change_metrics(self, rec_a, rec_b):
        # Changes to examine?
        #  - number/identity of individually detected features
        #  - numerical details regarding the detected features (position, type, etc??)
        #  - hierarchical structure of the features (e.g. different assigned parents?)
        #  - non-hierarchical annotations on the features

        ## TODO
        # 1. Compare only the ID fields from each record.
        #   Currently, they are sorted.
        rec_a_ID_list = rec_a.data
        rec_b_ID_list = rec_b.data
        a_len = len(rec_a_ID_list)
        b_len = len(rec_b_ID_list)

        additions = 0
        deletions = 0
        # changes = 0 

        # loop over rec a list; compare lexicographic order; if equal, advance both markers
        idx_a = 0
        idx_b = 0
        while idx_a < a_len and  idx_b < b_len # TODO the condition
            id_a = rec_a_ID_list[idx_a]
            id_b = rec_b_ID_list[idx_b]
            if id_a == id_b:
                idx_a += 1
                idx_b == 1
            elif id_a > id_b:
                idx_b += 1
                deletions += 1
            elif id_b > id_a:
                idx_a += 1
                additions += 1
                idx_a += 1
        else:
            additions += a_len - idx_a
            deletions += b_len - idx_b
                
        # this is not terribly meaningful if the two lists have substantially different sizes
        frac_changed = (additions + deletions) / (a_len + b_len)

        return {
            'additions': additions,
            'deletions': deletions,
            'frac_changed': frac_changed,
        }


def run_gff_change_ana(path_a, path_b):
    comparisons = [(path_a, path_b)]
    differ = dacman.DataDiffer(comparisons, dacman.Executor.DEFAULT)
    differ.use_plugin(GffPlugin)
    differ.start()


if __name__ == '__main__':
    cli_args = sys.argv[1:]
    path_a, path_b = cli_args[0], cli_args[1]
    run_gff_change_ana(path_a, path_b)
