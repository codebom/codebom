import os.path
import io
import re

def _ngrams(xs, n):
       return zip(*[xs[i:] for i in range(n)])

_WORDS_THRESHOLD = 0.9
def _license_ngrams_matched_from_words(license_words, templ_words, n):

    # If the proposed file has significantly fewer words than the template text,
    # assume it is not a match.
    if len(license_words) < _WORDS_THRESHOLD * len(templ_words):
        return 0, 1

    # Use a set to make the lookup O(1) instead of O(n)
    templSet = set(templ_words)

    license_words = [x for x in license_words if x in templSet]

    # If the filtered file has significantly fewer words than the template text,
    # assume it is not a match.
    if len(license_words) < _WORDS_THRESHOLD * len(templ_words):
        return 0, 1

    templ_grams = set(_ngrams(templ_words, n))
    license_grams = set(_ngrams(license_words, n))

    return len(templ_grams & license_grams), len(templ_grams)

def _license_ngrams_matched(license_text, license_templ, n):
    return _license_ngrams_matched_from_words(license_text.split(), license_templ.split(), n)

def _read_file(path):
    with io.open(path, 'r', encoding='utf-8') as hdl:
        return hdl.read()

_CLOSE_MATCH_THRESHOLD = 0.9
def _identify_license_text(license_words, template_words_map):
    """
    Return a tuple containing the license ID of the closest match to the
    input text (or None), and the percentage of matched grams. The
    percentage can be used as a rough gauge of confidence. A percentage above
    90% seems to be a good indicator that the license ID is accurate.
    """
    ngram_matches = {id: _license_ngrams_matched_from_words(license_words, words, 3) for id, words in template_words_map.items()}

    if not ngram_matches:
        return None, 0

    def _get_score(id):
        matched_len, templ_len = ngram_matches.get(id)
        # Note: For Python 2.7, either operand must be of type float.
        return matched_len / float(templ_len)

    close_matches = {id: val for id, val in ngram_matches.items() if _get_score(id) > _CLOSE_MATCH_THRESHOLD}

    if close_matches:
        # Of the close matches, find the one with the most matching N-grams.
        best_id = max(close_matches, key=lambda id: ngram_matches.get(id)[0])
    else:
        best_id = max(ngram_matches, key=_get_score)

    return best_id, _get_score(best_id)

def _template_path(license_id):
    return os.path.join(os.path.dirname(__file__), 'licenses', license_id + '.txt')

def _delete_template_variables(s):
    """
    Return the input string without references to variables.
    """
    return re.sub('<.+>', '', s)

def _make_template_words(id):
    text = _delete_template_variables(_read_file(_template_path(id)))
    return text.split()

def _make_template_words_map(license_ids):
    return {id: _make_template_words(id) for id in license_ids if os.path.isfile(_template_path(id))}

# A cache mapping a list of license IDs to a dictionary that maps a license ID to the words in its template.
_template_words_map_map = {}

def _lookup_template_words_map(license_ids):
    global _template_words_map_map
    key = ','.join(license_ids)
    if key not in _template_words_map_map:
        _template_words_map_map[key] = _make_template_words_map(license_ids)
    return _template_words_map_map[key]

def identify_license(license_path, license_ids):
    """
    Return a tuple containing the license ID of the closest match to the
    input text (or None), and the percentage of matched grams.
    """
    try:
        license_text = _read_file(license_path)
    except UnicodeDecodeError:
        return None, 0

    return _identify_license_text(license_text.split(), _lookup_template_words_map(license_ids))
