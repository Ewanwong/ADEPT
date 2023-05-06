import argparse
import nltk
import regex as re
from tqdm import tqdm
from collections import defaultdict
import random


def main():

    random.seed(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True,
                        help='Data')
    args = parser.parse_args()

    pat = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""")

    input_path = 'sentences_collection/gpt2/gender/' + args.input + '/filtered_lines.txt'
    output_path = 'sentences_collection/gpt2/gender/' + args.input + '/gender_swapped_filterd_lines.txt'
    
    with open('data/male.txt', 'r', encoding='utf-8') as f:
        male_words = f.read().split('\n')
    with open('data/female.txt', 'r', encoding='utf-8') as f:
        female_words = f.read().split('\n')

    assert len(male_words) == len(female_words)
    male2female, female2male = defaultdict(list), defaultdict(list)
    for male_word, female_word in zip(male_words, female_words):
        
        male2female[male_word].append(female_word)
        female2male[female_word].append(male_word)

    

    with open(input_path, 'r', encoding='utf-8') as f:
        sents = f.read().strip().split('\n')

    # by frequency
    count = {}
    all_tokens = [tok.strip().lower() for sent in sents for tok in re.findall(pat, sent)]
    for attribute in list(set(male_words + female_words)):
        count[attribute] = all_tokens.count(attribute) + 1 # smoothing
    male_weights = {}
    for male_word in male_words:
        female_words_list = male2female[male_word]
        weights = [count[i] for i in female_words_list]
        add =  sum(weights)
        weights = [count/add for count in weights]
        male_weights[male_word] = weights
    
    female_weights = {}
    for female_word in female_words:
        male_words_list = female2male[female_word]
        weights = [count[i] for i in male_words_list]
        add =  sum(weights)
        weights = [count/add for count in weights]
        female_weights[female_word] = weights
    

    # print(count)

    gender_swapped_sents = []
    for sent in tqdm(sents):
        toks = [tok.strip() for tok in re.findall(pat, sent)]
        # this is to make sure the transformed text has the same tokenization as original text
        prefix_length = len(toks[0])
        prefix = toks[0]
        intervals = [0] # record where to put whitespace
        for i in range(1, len(toks)):
            if prefix_length+len(toks[i])+1 > len(sent):
                intervals.append(0)
                prefix += toks[i]
                prefix_length += len(toks[i])
            elif prefix + ' ' + toks[i] == sent[:prefix_length+len(toks[i])+1]:
                intervals.append(1)
                prefix = prefix + ' ' + toks[i]
                prefix_length += len(toks[i]) + 1
            else:
                intervals.append(0)
                prefix += toks[i]
                prefix_length += len(toks[i])
        
        swapped_sent = []
        for tok in toks:
            if tok.lower() in male_words:
                swapped_list = male2female[tok.lower()]
                
                swapped = random.choices(swapped_list, weights=male_weights[tok.lower()], k=1)[0]

                if tok[0] != tok.lower()[0]:
                    swapped = swapped.capitalize()
                swapped_sent.append(swapped)
            elif tok.lower() in female_words:
                swapped_list = female2male[tok.lower()]

                swapped = random.choices(swapped_list, weights=female_weights[tok.lower()], k=1)[0]
                
                if tok[0] != tok.lower()[0]:
                    swapped = swapped.capitalize()
                swapped_sent.append(swapped)
            else:
                swapped_sent.append(tok)
        assert len(toks) == len(swapped_sent)

        # add white spaces
        new_sent = ''
        for i in range(len(toks)):
            new_sent = new_sent + ' '*intervals[i] + swapped_sent[i]
        gender_swapped_sents.append(new_sent)
        # gender_swapped_sents.append(' '.join(swapped_sent))

    #TODO: add name swapping
    
    with open(output_path, 'w') as f:
        for sent in gender_swapped_sents:
            f.write(sent)
            f.write('\n')

if __name__ == '__main__':
    main()