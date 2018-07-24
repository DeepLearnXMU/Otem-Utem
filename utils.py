# coding=utf-8

import os
import math
import sys
from collections import defaultdict

# Get reference files, ref indicates the path, following the multi-bleu tradition
def get_refs(ref):
    refs = []

    # return the existed reference file
    if os.path.exists(ref):
        refs.append(ref)
    else:
        # the reference does not exist, check whether the indexed file exist
    	if not os.path.exists(ref+"0"):
            print >> sys.stderr, 'Error: could not find proper reference file ', ref+"0"
            sys.exit(1)
        # enumerate all possible references
    	while True:
            cur_file = ref+"%d" % len(refs)
            if not os.path.exists(cur_file): break
            refs.append(cur_file)
    return refs

# An interface for tokenization, currently we rely on external tokenizers
# i.e. We assume all the inputs have been well-tokenized
def tokenize(s): return s.split()

# Reading all contents inside the file `f`, "lc" tells whether open the 'lower case' function 
def read(f, lc=False):
    return [tokenize(line.strip()) if not lc else tokenize(line.strip().lower())
            for line in file(f, 'rU').readlines()]

# Read all ngrams inside the sentences, default up to 4.
def get_ngram_list(sentence, ngram=4):
    ngram_dict = defaultdict(int)
    for n in xrange(1, ngram+1):
        for start in xrange(0, len(sentence) - (n - 1)):
            ngram = ' '.join(sentence[start:start + n])
            ngram_dict[ngram] += 1
    return ngram_dict

# Generate some common strategies to deal with multiple references
def common_strategies(choices):
    return {'min': min(choices),
			'max': max(choices),
			'avg': sum(choices) * 1. / len(choices)
	}

# When multiple references exist, return the length of a preferred references
def get_length_reference(ref_lengths, cand_length, strategy="best_match"):
    # different strategy, no one is absolutely correct
    strategies = common_strategies(ref_lengths)

    # the best matched cases
    length, diff = 9999, 9999
    for r in ref_lengths:
        d = abs(r - cand_length)

        if d < diff:
            length, diff = r, d
        elif d == diff:
            if r < length:
                length = r
    strategies['best_match'] = length

    return strategies[strategy]

# Deal with invalid inputs
def safe_log(d):
    if d <= 0:
        print >> sys.stderr, "WARNING, a non-positive number is processed by log"
        return -9999999999

    return math.log(d)
