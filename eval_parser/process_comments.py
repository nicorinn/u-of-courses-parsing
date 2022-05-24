from flair.models import TextClassifier
from flair.data import Sentence
from operator import itemgetter
import re
import yake

# YAKE setup
classifier = TextClassifier.load('en-sentiment')
kw_extractor = yake.KeywordExtractor()
language = "en"
max_ngram_size = 3
deduplication_threshold = 0.9
num_keywords = 25
custom_kw_extractor = yake.KeywordExtractor(
    lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=num_keywords, features=None)

unwanted_keywords = ['class', 'lecture', 'lectures', 'knowledge', 'understanding',
                     'learn', 'learning', 'learned', 'prof', 'lot', 'made', 'professor',
                     'exam', 'midterm', 'make', 'thing', 'person', 'understand']


def process_comments(data_dict, soup):
    comments = []

    total_score = 0
    instructor_names = create_instructor_name_dict(data_dict['instructors'])

    for table in soup.find_all('table'):
        if table.thead.tr.th.get_text() == 'Comments':
            for row in table.tbody.find_all('tr'):
                comment = row.td.get_text()
                total_score += get_sentiment_score(comment, classifier)
                comments.append(comment)

    comments_text = '. '.join(comments)
    keywords = custom_kw_extractor.extract_keywords(comments_text)
    refined_keywords = refine_keywords(
        keywords, instructor_names, unwanted_keywords)

    data_dict['chart_data']['keywords'] = refined_keywords
    if len(comments) == 0:
        data_dict['sentiment'] = 0
    else:
        data_dict['sentiment'] = total_score / len(comments)


def add_comment_keywords(keyword_dict, comment_keywords, instructor_names):
    for word in comment_keywords:
        if word in instructor_names:
            return
        if word in keyword_dict:
            keyword_dict[word] += 1
        else:
            keyword_dict[word] = 1


def get_sentiment_score(comment, classifier):
    sentence = Sentence(comment)
    classifier.predict(sentence)
    score = sentence.labels[0].score
    if sentence.labels[0].value == 'NEGATIVE':
        score = score * -1
    return score


def get_comment_keywords(comment, tagger):
    sentence = Sentence(comment)
    tagger.predict(sentence)

    keywords = []
    for entity in sentence.get_spans('ner'):
        keywords.append(entity.text)
    return keywords


def process_comment_words(data_dict, comment, instructor_names):
    alpha_only_comment = re.sub('[^a-zA-Z]+', ' ', comment.lower())
    comment_words = alpha_only_comment.split()
    for word in comment_words:
        if (word not in instructor_names):
            if word in data_dict['words']:
                data_dict['words'][word] += 1
            else:
                data_dict['words'][word] = 1


def create_instructor_name_dict(instructors):
    """ Generates a dictionary with instructor first, last, and full names

    Args:
        instructors (List[string]): List of full names of instructors

    Returns:
        _type_: Dictionary with instructor first, last, and full names as keys
    """
    names = {}
    for name in instructors:
        names[name.lower()] = True
        for subname in name.split():
            names[subname.lower()] = True
    return names


def refine_keywords(keywords, instructor_names, unwanted_keywords):
    refined_keywords = []
    for word in keywords:
        if word[0].lower() not in instructor_names and word[0].lower() not in unwanted_keywords:
            refined_keywords.append(word)
    refined_keywords.sort(key=itemgetter(1))
    length = num_keywords if len(
        refined_keywords) >= num_keywords else len(refined_keywords)

    return refined_keywords[:length]
