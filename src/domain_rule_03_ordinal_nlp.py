"""
domain_rule_03_ordinal_nlp.py

Natural language processing functionality for rule 03 (ordinal sort)
"""


from nltk.corpus import wordnet as wn
from nltk import word_tokenize, pos_tag
import logging

"""
This code is reused from https://nlpforhackers.io/wordnet-sentence-similarity/ (and fixed!)
The algorithm is proposed by Mihalcea et al. in the paper “Corpus-based and Knowledge-based Measures
of Text Semantic Similarity” (https://www.aaai.org/Papers/AAAI/2006/AAAI06-123.pdf)
"""


def penn_to_wn(tag):
    """ Convert between a Penn Treebank tag to a simplified Wordnet tag """
    if tag.startswith('N'):
        return 'n'

    if tag.startswith('V'):
        return 'v'

    if tag.startswith('J'):
        return 'a'

    if tag.startswith('R'):
        return 'r'

    return None


def tagged_to_synset(word, tag):
    wn_tag = penn_to_wn(tag)
    if wn_tag is None:
        return None

    try:
        return wn.synsets(word, wn_tag)[0]
    except:
        return None


def sentence_similarity(sentence1, sentence2):
    """ compute the sentence similarity using Wordnet """
    # Tokenize and tag
    sentence1 = pos_tag(word_tokenize(sentence1))
    sentence2 = pos_tag(word_tokenize(sentence2))

    # Get the synsets for the tagged words
    synsets1 = [tagged_to_synset(*tagged_word) for tagged_word in sentence1]
    synsets2 = [tagged_to_synset(*tagged_word) for tagged_word in sentence2]

    # Filter out the Nones
    synsets1 = [ss for ss in synsets1 if ss]
    synsets2 = [ss for ss in synsets2 if ss]

    score, count = 0.0, 0

    # For each word in the first sentence
    for synset in synsets1:
        # Get the similarity value of the most similar word in the other sentence
        # verde fix... best_score = max([synset.path_similarity(ss) for ss in synsets2])
        similarities = [synset.path_similarity(ss) for ss in synsets2]
        similarities = list(filter(None, similarities))

        if similarities:
            best_score = max(similarities)
        else:
            best_score = None

        # Check that the similarity could have been computed
        if best_score is not None:
            score += best_score
            count += 1

    # Average the values
    score = score / count if count > 0 else 0  # verde fix
    return score


def symmetric_sentence_similarity(sentence1, sentence2):
    """ compute the symmetric sentence similarity using Wordnet """
    logging.debug(f'getting symmeetric sentence similarity for {[sentence1, sentence2]}')
    sim = (sentence_similarity(sentence1, sentence2) + sentence_similarity(sentence2, sentence1)) / 2
    logging.debug(f'similarity is {sim}')
    return sim


"""
end of code reuse as described by comment at top of file
"""


def order_source_data_terms(source_terms, domain_terms):
    """
    Takes a list of unordered terms from a source data set (e.g. ['big', 'little', 'middle']),
    and a list of ordered domain terms (e.g.  ['small', 'medium', 'large']). Returns the source terms
    in a domain influenced order (i.e. ['little', 'middle', 'big']).
    :param source_terms: unordered terms from the source data
    :param domain_terms: ordered domain terms
    :return: list of ordered source terms
    """

    logging.info(f'using WordNet to sort {source_terms} based on {domain_terms}')
    source_domain_map = {}

    # for each source term get the most similar domain term
    for source_term in source_terms:
        max_similarity = 0.0
        for domain_term_id, domain_term in enumerate(domain_terms):
            similarity = symmetric_sentence_similarity(source_term, domain_term)
            if similarity >= max_similarity:
                source_domain_map[source_term] = (source_term, domain_term_id, similarity)
                max_similarity = similarity

    # sort the source terms based on their mapped domain terms and similarities (if one-to-many)
    term_map = list(source_domain_map.values())
    sorted_source_terms = [term[0] for term in sorted(term_map, key=lambda x: (x[1], x[2]))]
    assert sorted(source_terms) == sorted(sorted_source_terms), 'lost values in NLP ordinal sorting'
    logging.info(f'proposed sort order is {sorted_source_terms}')
    return sorted_source_terms


if __name__ == '__main__':

    # a little test case

    domain_ordinal = ['small', 'medium', 'large']
    source_cats = ['big', 'little', 'middle']

    print('domain', domain_ordinal)
    print('source', source_cats)
    print('source sorted', order_source_data_terms(source_cats, domain_ordinal))
