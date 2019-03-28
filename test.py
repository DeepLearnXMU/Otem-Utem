# coding=utf-8

from metric import bleu, otem, utem


ref = "You should learn to use the computer ."

can1 = "You should learn to use the car ."
can2 = "You should learn to use the the computer ."
can3 = "You should learn to use the ."

print('Reference: {}'.format(ref))
print('Candidate1: {}'.format(can1))
print('Candidate2: {}'.format(can2))
print('Candidate3: {}'.format(can3))

refs = [[ref.split()]]
can1 = [can1.split()]
can2 = [can2.split()]
can3 = [can3.split()]

print('BLEU {} vs {} vs {}'.format(bleu(can1, refs), bleu(can2, refs), bleu(can3, refs)))
print('OTEM {} vs {} vs {}'.format(otem(can1, refs, n=1), otem(can2, refs, n=1), otem(can3, refs, n=1)))
print('UTEM {} vs {} vs {}'.format(utem(can1, refs), utem(can2, refs), utem(can3, refs)))
