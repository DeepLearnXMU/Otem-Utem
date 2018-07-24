#! /usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import math

from collections import defaultdict
from utils import *


# strategy selection
def get_ngram_overmatch(overmatch_ngram_count, match_strategy=min):
    overmatch_value = 0

    match_strategy_list = common_strategies(overmatch_ngram_count)

    if match_strategy in match_strategy_list:
        overmatch_value = match_strategy_list[match_strategy]
    else:
        print >> sys.stderr, 'ERROR: unsupported strategy for over-translation match'
        sys.exit(1)

    return overmatch_value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='over-translation evaluation metric (OTEM) on multiple references.')
    parser.add_argument('-lc', help='Lowercase, i.e case-insensitive setting', action='store_true')
    parser.add_argument('-ms', help='over-translation match strategy', default='min')
    parser.add_argument('-v', help='print other useful information in the calculation procedure', action="store_true")
    parser.add_argument('candidate', help='Reads the candidate generated by MT system')
    parser.add_argument('reference', help='Reads the references from reference or reference0, reference1, ...')

    args = parser.parse_args()

    cand = args.candidate
    refs = get_refs(args.reference)
    match_strategy, verbose = args.ms, args.v

    cand_sentences = read(cand, args.lc)
    refs_sentences = [read(ref, args.lc) for ref in refs]

    assert len(cand_sentences) == len(refs_sentences[0]), \
        'ERROR: the length of candidate and reference must be the same.'

    length_candidate = 0        # total length of candidate
    length_reference = 0        # total length of references, determined by the "match_strategy"
    total_ngram_count_per_corpus, overmatch_ngram_count_per_corpus = defaultdict(int), defaultdict(int)

    # scan all candidates in the corpus
    for trs_idx, cand_sentence in enumerate(cand_sentences):
        length_cand_sentence = len(cand_sentence)
        if verbose:
            print '%d. candidate: %s' %(trs_idx, cand_sentence)

        # get all n-grams in current candidate from n = 1...4
        cand_ngrams = get_ngram_list(cand_sentence)
        length_candidate += length_cand_sentence

        lengths_of_all_references = []  # length list of the references corresponding to current candidate
        total_ngram_count_per_sentence, overmatch_ngram_count_per_sentence = defaultdict(int), defaultdict(list)

        # scan all references corresponding to current candidate
        for ref_idx, ref_sentences in enumerate(refs_sentences):
            reference = ref_sentences[trs_idx]  # current reference

            length_ref_sentence = len(reference)
            lengths_of_all_references.append(length_ref_sentence)

            ref_ngrams = get_ngram_list(reference)  # get all n-grams in current reference from n = 1...4
            total_ngram_count_per_reference, overmatch_ngram_count_per_reference = defaultdict(int), defaultdict(int)

            # count the number of over-translation n-grams in current candidate compared with current reference
            for ngram in cand_ngrams:
                n = len(ngram.split())

                cand_ngram_count = cand_ngrams[ngram]  # the number of occurrences of n-gram in current candidate
                total_ngram_count_per_reference[n] += cand_ngram_count

                # case 1: current n-gram doesn't appear in current reference at all,
                #         but appears in current candidate more than once
                if ngram not in ref_ngrams:
                    if cand_ngrams[ngram] > 1:
                        overmatch_ngram_count_per_reference[n] += cand_ngram_count - 1
                elif cand_ngram_count > ref_ngrams[ngram]:
                    # case 2: the n-gram occurs in both reference and candidate, but the occurrence is more in candidate
                    overmatch_ngram_count_per_reference[n] += cand_ngram_count - ref_ngrams[ngram]

            if verbose:
                print 'ref%d: %s' % (ref_idx, " ".join(reference))
                print 'overmatch n-gram count: [n=1: %d; n=2: %d; n=3: %d; n=4: %d]' % \
                                        (overmatch_ngram_count_per_reference[1],
                                         overmatch_ngram_count_per_reference[2],
                                         overmatch_ngram_count_per_reference[3],
                                         overmatch_ngram_count_per_reference[4])
                print 'total n-gram count: [n=1: %d; n=2: %d; n=3: %d; n=4: %d]' % \
                                        (total_ngram_count_per_reference[1],
                                         total_ngram_count_per_reference[2],
                                         total_ngram_count_per_reference[3],
                                         total_ngram_count_per_reference[4])

            for n in total_ngram_count_per_reference:
                total_ngram_count_per_sentence[n] += total_ngram_count_per_reference[n]
                overmatch_ngram_count_per_sentence[n].append(overmatch_ngram_count_per_reference[n])

        length_reference += get_length_reference(lengths_of_all_references, length_cand_sentence)  # get the best match length

        for n in total_ngram_count_per_sentence:
            total_ngram_count_per_corpus[n] += total_ngram_count_per_sentence[n]
            overmatch_ngram_count_per_corpus[n] += get_ngram_overmatch(overmatch_ngram_count_per_sentence[n], match_strategy)

        if verbose:
            print 'with match strategy: %s' % match_strategy
            print 'final overmatch n-gram count: [n=1: %d; n=2: %d; n=3: %d; n=4: %d]' % \
                                        (overmatch_ngram_count_per_corpus[1],
                                         overmatch_ngram_count_per_corpus[2],
                                         overmatch_ngram_count_per_corpus[3],
                                         overmatch_ngram_count_per_corpus[4])
            print 'final total n-gram count: [n=1: %d; n=2: %d; n=3: %d; n=4: %d]' % \
                                        (total_ngram_count_per_corpus[1],
                                         total_ngram_count_per_corpus[2],
                                         total_ngram_count_per_corpus[3],
                                         total_ngram_count_per_corpus[4])
            print '--------------------------------------------------------------------------------------------------'

    length_penalty = 1
    otem = 0
    multi_otem = defaultdict(int)

    for n in xrange(1, 5):
        if n in total_ngram_count_per_corpus:
            multi_otem[n] += overmatch_ngram_count_per_corpus[n] * 1. / total_ngram_count_per_corpus[n]

    if length_reference == 0:
        print >> sys.stderr, "OTEM = 0, 0/0/0/0 (LP=0, ratio=0, hyp_len=0, ref_len=0)"
        sys.exit(1);

    # Over-translation: candidate prefered to be longer, so penalize long translations
    if length_candidate >= length_reference:
        length_penalty = math.exp(1. - length_reference*1./length_candidate)

    # We observed that litter 4-grams appear in this case, so we converted to bigrams.
    # otem = length_penalty * math.exp((safe_log(multi_otem[1]) +
    #                                   safe_log(multi_otem[2]) +
    #                                   safe_log(multi_otem[3]) +
    #                                   safe_log(multi_otem[4])) / 4.)

    otem = length_penalty * math.exp((safe_log(multi_otem[1]) +
                                      safe_log(multi_otem[2])) / 2.)


    print >> sys.stderr, "OTEM = %.2f, %.1f/%.1f/%.1f/%.1f (LP=%.3f, ratio=%.3f, hyp_len=%d, ref_len=%d)" %( \
            100*otem, \
            100*multi_otem[1], \
            100*multi_otem[2], \
            100*multi_otem[3], \
            100*multi_otem[4], \
            length_penalty*1., \
            length_candidate*1. / length_reference, \
            length_candidate, \
            length_reference)