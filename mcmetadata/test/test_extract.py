import unittest
import datetime as dt
import time

import mcmetadata
from .. import extract
from .. import webpages
from .. import content


class TestExtract(unittest.TestCase):

    def tearDown(self):
        time.sleep(1)  # sleep time in seconds

    def test_shortened(self):
        results = extract(url="http://nyti.ms/4K9g6u")
        assert 'is_shortened' in results
        assert results['is_shortened'] is True
        assert results['original_url'] == "http://nyti.ms/4K9g6u"
        assert results['url'] != "http://nyti.ms/4K9g6u"

    def test_homepage(self):
        results = extract(url="https://web.archive.org/web/")
        assert 'is_homepage' in results
        assert results['is_homepage'] is True

    def test_no_date(self):
        # Fail gracefully for webpages that aren't news articles, and thus don't have publication dates
        results = extract(url="https://web.archive.org/web/https://example.com/")
        assert 'publication_date' in results
        assert results['publication_date'] is None
        assert 'is_homepage' in results
        assert results['is_homepage'] is False

    def test_observers(self):
        webpages.DEFAULT_TIMEOUT_SECS = 30  # for some reason this one takes longer
        test_url = "https://web.archive.org/web/https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        results = extract(test_url)
        assert 'publication_date' in results
        assert results['publication_date'] == dt.datetime(2019, 8, 27, 0, 0)
        assert 'text_content' in results
        assert len(results['text_content']) > 7000
        assert 'text_extraction_method' in results
        assert results['text_extraction_method'] == content.METHOD_TRAFILATURA
        assert 'canonical_domain' in results
        assert results['canonical_domain'] == 'france24.com'
        assert 'article_title' in results
        assert results['article_title'] == 'African migrants trapped in Mexico protest for right to travel to USA'
        assert 'language' in results
        assert results['language'] == 'en'
        assert 'original_url' in results
        assert results['original_url'] == "https://web.archive.org/web/https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey"
        assert 'url' in results
        assert results['url'] == 'https://observers.france24.com/en/20190826-mexico-african-migrants-trapped-protest-journey'

    def test_archived_url(self):
        # properly handle pages at web archives (via memento headers)
        test_url = "https://web.archive.org/web/https://www.nytimes.com/interactive/2018/12/10/business/location-data-privacy-apps.html"
        results = extract(test_url)
        assert 'canonical_domain' in results
        assert results['canonical_domain'] == 'nytimes.com'
        assert 'original_url' in results
        assert results['url'] == 'https://www.nytimes.com/interactive/2018/12/10/business/location-data-privacy-apps.html'

    def test_language(self):
        url = "https://web.archive.org/web/https://www.mk.co.kr/news/society/view/2020/07/693939/"
        results = extract(url)
        assert 'language' in results
        assert results['language'] == 'ko'

    def test_regionalized_language(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        results = extract(url)
        assert "pt" == results['language']
        assert "pt-br" == results['full_language']

    def test_redirected_url(self):
        url = "https://api.follow.it/track-rss-story-click/v3/ecuhSAhRa8kTTPWTA7xaXioxzwoq1nFt"
        results = extract(url)
        assert url == results['original_url']
        final_url = "https://www.trussvilletribune.com/2022/03/02/three-students-from-center-point-receive-academic-scholarships/"
        assert final_url == results['url']
        assert "trussvilletribune.com" == results['canonical_domain']
        assert results['normalized_url'] == "http://trussvilletribune.com/2022/03/02/three-students-from-center-point-receive-academic-scholarships/"
        assert results['language'] == 'en'


class TestStats(unittest.TestCase):

    def test_total_works(self):
        url = "https://web.archive.org/web/http://entretenimento.uol.com.br/noticias/redacao/2019/08/25/sem-feige-sem-stark-o-sera-do-homem-aranha-longe-do-mcu.htm"
        _ = extract(url)
        assert mcmetadata.stats.get('total') > 0
        for s in mcmetadata.STAT_NAMES:
            assert s in mcmetadata.stats  # stat is recorded
            assert mcmetadata.stats.get(s) > 0  # has real data
            if s != 'total':  # is less than total
                assert mcmetadata.stats.get('url') < mcmetadata.stats.get('total')


if __name__ == "__main__":
    unittest.main()
