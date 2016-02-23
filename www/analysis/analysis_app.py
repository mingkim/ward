# The MIT License (MIT)
#
# Copyright (c) 2015 pjwards.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==================================================================================
""" Provides analysis app class """

import analysis.analysis_core as core
from django.db.models import Q
from .models import ArchiveAnalysisWord, AnticipateArchive, AnalysisDBSchema
from archive.models import Group, Post, Comment, Attachment


def add_anticipate_list(data_object):
    """
    add analyzed article to db
    :param data_object: data object of target article
    """
    newarticle = AnticipateArchive(group=data_object.group)
    newarticle.id = data_object.id
    newarticle.user = data_object.user
    newarticle.message = data_object.message
    newarticle.time = data_object.created_time
    newarticle.save()


def add_words_db(group, word_set):
    for word in word_set:
        if not ArchiveAnalysisWord.objects.filter(group=group, word=word).exists():
            ArchiveAnalysisWord(group=group, word=word).save()
        else:
            exword = ArchiveAnalysisWord.objects.filter(group=group, word=word)[0]
            exword.count += 1
            exword.save()


def get_average_like_and_comment(group, is_post=False, is_comment=False):
    """
    get or make average likes and comments count of posts or comments
    :param group: group object
    :return: array of average likes and comments
    """
    basicdata = AnalysisDBSchema.objects.filter(group=group)[0]         # consider update time (standard = created)

    if is_post is True:
        posts = Post.objects.filter(group=group)
        if basicdata is not None:                       # need update periodically
            if basicdata.avgpostcomment is not 0 and basicdata.avgpostlike is not 0:
                likes = 0
                comments = 0
                counts = posts.count()

                for apost in posts:
                    likes += apost.like_count
                    comments += apost.comment_count

                avglike = int(likes / counts)
                avgcomt = int(comments / counts)

                basicdata.avgpostlike = avglike
                basicdata.avgpostcomment = avgcomt
                basicdata.save()
            else:
                avglike = basicdata.avgpostlike
                avgcomt = basicdata.avgpostcomment
        else:
            basicdata = AnalysisDBSchema(group=group)

            likes = 0
            comments = 0
            counts = posts.count()

            for apost in posts:
                likes += apost.like_count
                comments += apost.comment_count

            avglike = int(likes / counts)
            avgcomt = int(comments / counts)

            basicdata.avgpostlike = avglike
            basicdata.avgpostcomment = avgcomt
            basicdata.save()

    elif is_comment is True:
        commentlist = Comment.objects.filter(group=group)
        if basicdata is not None:                       # need update periodically
                if basicdata.avgcomtcomment is not 0 and basicdata.avgcomtlike is not 0:
                    likes = 0
                    comments = 0
                    counts = commentlist.count()

                    for apost in commentlist:
                        likes += apost.like_count
                        comments += apost.comment_count

                    avglike = int(likes / counts)
                    avgcomt = int(comments / counts)

                    basicdata.avgcomtlike = avglike
                    basicdata.avgcomtcomment = avgcomt
                    basicdata.save()
                else:
                    avglike = basicdata.avgcomtlike
                    avgcomt = basicdata.avgcomtcomment
        else:
            basicdata = AnalysisDBSchema(group=group)

            likes = 0
            comments = 0
            counts = commentlist.count()

            for apost in commentlist:
                likes += apost.like_count
                comments += apost.comment_count

            avglike = int(likes / counts)
            avgcomt = int(comments / counts)

            basicdata.avgcomtlike = avglike
            basicdata.avgcomtcomment = avgcomt
            basicdata.save()

    else:
        return None

    returnarry = [avglike, avgcomt]
    return returnarry


def analyze_hit_article(analyzer, group, article_set, is_post=False, is_comment=False):
    """
    analyze article
    :param analyzer: analyzer for analysis
    :param group: group object
    :param article_set: list of articles
    :return string of status
    """
    for article in article_set:                # better algorithm
        if is_post is True:
            attach = Attachment.objects.filter(post=article)
            if attach is None:
                if article.message is None:
                    return "no_message"

                words = core.analyze_articles(analyzer, article.message)
                add_words_db(group, words)
            else:
                if attach.description is not None:
                    message = attach.description
                elif attach.title is not None:
                    message = attach.title
                else:
                    return "no_message"

                words = core.analyze_articles(analyzer, message)
                add_words_db(group, words)

        elif is_comment is True:
            attach = Attachment.objects.filter(comment=article)
            if attach is None:
                if article.message is None:
                    return "no_message"

                words = core.analyze_articles(analyzer, article.message)
                add_words_db(group, words)
            else:
                if attach.description is not None:
                    message = attach.description
                elif attach.title is not None:
                    message = attach.title
                else:
                    return "no_message"

                words = core.analyze_articles(analyzer, message)
                add_words_db(group, words)
        else:
            return "no_article"


def analyze_feed(analyzer, data_object):
    if data_object.message is not None:
        message = data_object.message
    else:
        message = ''

    if 'attachment' in data_object:
        attach = data_object.get('attachment')
        if 'description' in attach:
            attach_message = attach.get('description')
        elif 'title' in attach:
            attach_message = attach.get('title')
        else:
            attach_message = ''
    else:
        attach_message = ''

    message_word_set = core.analyze_articles(analyzer, message)
    attach_word_set = core.analyze_articles(analyzer, attach_message)
    temp_set = message_word_set + attach_word_set
    word_set = list(set(temp_set))      # make better algorithm

    word_db = ArchiveAnalysisWord.objects.filter(group=data_object.group)
    data_set = [sp.word for sp in word_db]

    for i in word_set:                   # make better algorithm
        if i in data_set:
            return word_set

    return None


def analysis_prev_hit_posts(group):
    """
    analysis previous posts that have high likes and comments
    :param group: group object
    """
    avgarry = get_average_like_and_comment(group, is_post=True)           # or Admin manage this directly

    if avgarry is None:
        print("get_average function fail")
        return

    hits = Post.objects.filter(Q(group=group), Q(like_count__gte=avgarry[0]) | Q(comment_count__gte=avgarry[1]))
    # better accuracy

    analyzer = core.AnalysisDiction(True, True)

    analyze_hit_article(analyzer, group, hits, is_post=True)


def analysis_prev_hit_comments(group):
    """
    analysis previous comments that have high likes and comments
    :param group: group object
    """
    avgarry = get_average_like_and_comment(group, is_comment=True)           # or Admin manage this directly

    if avgarry is None:
        print("get_average function fail")
        return

    hits = Comment.objects.filter(Q(group=group), Q(like_count__gte=avgarry[0]) | Q(comment_count__gte=avgarry[1]))

    analyzer = core.AnalysisDiction(True, True)

    analyze_hit_article(analyzer, group, hits, is_comment=True)


def analyze_feed_sequence(data_object):
    analyzer = core.AnalysisDiction(True, True)

    if data_object.message is None:
        return "no_message"

    if AnticipateArchive(group=data_object.group, id=data_object.id).exists():
        return "exist"

    words = analyze_feed(analyzer, data_object)
    if words is None:
        return "no_concern"

    add_anticipate_list(data_object=data_object)

    add_words_db(data_object.group, words)

    return "ok"


def run_app():
    print('hello')
    # analyze old post and comment and spam (make analyzer) - init sequence
    # get new feed
    # check if spam (make analyzer) - feed analyze sequence
    # go to spam app if it is spam
    # go to analysis app if it is not spam
    # analyze feed data and store anticipate db if it will be popular article
    # delete or restore spam sequence (make analyzer)   - spam sequence
    # add anticipate list sequence (make analyzer)  - analysis sequence
