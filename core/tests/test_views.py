from unittest.mock import patch
import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from django.utils import translation
from django.http import Http404
from django.views.generic import TemplateView

from core.mixins import CMSPageMixin
from core.mixins import GetSlugFromKwargsMixin
from core import helpers
from core.tests.helpers import create_response


test_sectors = [
    {
        'title': 'Aerospace',
        'featured': True,
        'meta': {
            'slug': 'invest-aerospace',
            'languages': [
                ['en-gb', 'English'],
                ['ar', 'العربيّة'],
                ['de', 'Deutsch'],
            ],
        },
    },
    {
        'title': 'Automotive',
        'featured': True,
        'meta': {
            'slug': 'invest-automotive',
            'languages': [
                ['en-gb', 'English'],
                ['fr', 'Français'],
                ['ja', '日本語'],
            ],
        },
    },
]

dummy_page = {
    'title': 'test',
    'meta': {
        'languages': [
            ['en-gb', 'English'],
            ['fr', 'Français'],
            ['de', 'Deutsch'],
        ]
    }
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_cms_language_switcher_one_language(mock_cms_response, rf):
    class MyView(CMSPageMixin, TemplateView):

        template_name = 'core/base.html'
        slug = 'test'
        active_view_name = ''

    page = {
        'title': 'test',
        'meta': {
            'languages': [
                ['de', 'Deutsch'],
            ]
        }
    }

    mock_cms_response.return_value = helpers.create_response(
        status_code=200,
        json_payload=page
    )

    request = rf.get('/')
    with translation.override('de'):
        response = MyView.as_view()(request)

    assert response.status_code == 200
    assert response.context_data['language_switcher']['show'] is False


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_cms_language_switcher_active_language_available(
    mock_cms_response, rf
):
    class MyView(CMSPageMixin, TemplateView):

        template_name = 'core/base.html'
        slug = 'test'
        active_view_name = ''

    mock_cms_response.return_value = helpers.create_response(
        status_code=200,
        json_payload=dummy_page
    )

    request = rf.get('/de/')
    with translation.override('de'):
        response = MyView.as_view()(request)

    assert response.status_code == 200
    context = response.context_data['language_switcher']
    assert context['show'] is True


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_active_view_name(mock_cms_response, rf):
    class TestView(CMSPageMixin, TemplateView):
        active_view_name = 'test'
        template_name = 'core/base.html'
        slug = 'test'

    mock_cms_response.return_value = helpers.create_response(
        status_code=200,
        json_payload=dummy_page
    )

    request = rf.get('/')
    response = TestView.as_view()(request)

    assert response.status_code == 200
    assert response.context_data['active_view_name'] == 'test'


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_get_cms_page(mock_cms_response, rf):
    class TestView(CMSPageMixin, TemplateView):
        template_name = 'core/base.html'
        slug = 'invest-home-page'
        active_view_name = ''

    mock_cms_response.return_value = helpers.create_response(
        status_code=200,
        json_payload=dummy_page
    )

    request = rf.get('/')
    response = TestView.as_view()(request)

    assert response.context_data['page'] == dummy_page


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_get_cms_page_kwargs_slug(mock_cms_response, rf):
    class TestView(GetSlugFromKwargsMixin, CMSPageMixin, TemplateView):
        template_name = 'core/base.html'
        active_view_name = ''

    page = {
        'title': 'the page',
        'meta': {
            'languages': [('en-gb', 'English'), ('de', 'German')],
            'slug': 'aerospace'
        },
    }

    mock_cms_response.return_value = helpers.create_response(
            status_code=200,
            json_payload=page
        )

    translation.activate('en-gb')
    request = rf.get('/')
    view = TestView.as_view()
    response = view(request, slug='aerospace')

    assert response.context_data['page'] == page


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_404_when_cms_language_unavailable(mock_cms_response, rf):
    class TestView(GetSlugFromKwargsMixin, CMSPageMixin, TemplateView):
        template_name = 'core/base.html'

    page = {
        'title': 'the page',
        'meta': {
            'languages': [('en-gb', 'English'), ('de', 'German')],
            'slug': 'aerospace'
        },
    }

    mock_cms_response.return_value = helpers.create_response(
            status_code=200,
            json_payload=page
        )

    translation.activate('fr')
    request = rf.get('/fr/')
    view = TestView.as_view()

    with pytest.raises(Http404):
        view(request, slug='aerospace')


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_article_detail_page_no_related_content(
    mock_get_page, client, settings
):
    test_article_page_no_related_content = {
        'title': 'Test article admin title',
        'article_title': 'Test article',
        'article_teaser': 'Test teaser',
        'article_body_text': '<p>Lorem ipsum</p>',
        'related_pages': [],
        'last_published_at': '2018-10-09T16:25:13.142357Z',
        'meta': {
            'languages': [('en-gb', 'English')],
            'slug': 'foo',
        },
        'page_type': 'InternationalArticlePage',
    }

    url = reverse(
        'article-detail',
        kwargs={'list': 'bar', 'slug': 'foo'}
    )

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload=test_article_page_no_related_content
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['core/article_detail.html']

    assert 'Related content' not in str(response.content)


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_article_detail_page_related_content(
    mock_get_page, client, settings
):

    article_page = {
        'title': 'Test article admin title',
        'article_title': 'Test article',
        'article_teaser': 'Test teaser',
        'article_image': {'url': 'foobar.png'},
        'article_body_text': '<p>Lorem ipsum</p>',
        'related_pages': [
            {
                'article_title': 'Related article 1',
                'article_teaser': 'Related article 1 teaser',
                'article_image_thumbnail': {'url': 'related_article_one.jpg'},
                'full_path': '/test-list/test-one/',
                'meta': {
                    'slug': 'test-one',
                }
            },
            {
                'article_title': 'Related article 2',
                'article_teaser': 'Related article 2 teaser',
                'article_image_thumbnail': {'url': 'related_article_two.jpg'},
                'full_path': '/test-list/test-two/',
                'meta': {
                    'slug': 'test-two',
                }
            },
        ],
        'meta': {
            'languages': [('en-gb', 'English')],
            'slug': 'foo',
        },
        'page_type': 'InternationalArticlePage',
    }

    url = reverse(
        'article-detail', kwargs={'list': 'bar', 'slug': 'foo'}
    )

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload=article_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['core/article_detail.html']

    assert 'Related content' in str(response.content)
    soup = BeautifulSoup(response.content, 'html.parser')

    assert soup.find(
        id='related-article-test-one-link'
    ).attrs['href'] == '/international/test-list/test-one/'
    assert soup.find(
        id='related-article-test-two-link'
    ).attrs['href'] == '/international/test-list/test-two/'

    assert soup.find(
        id='related-article-test-one'
    ).select('h3')[0].text == 'Related article 1'
    assert soup.find(
        id='related-article-test-two'
    ).select('h3')[0].text == 'Related article 2'


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_breadcrumbs_mixin(mock_get_page, client, settings):

    url = reverse('article-detail', kwargs={'list': 'bar', 'slug': 'foo'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload={
            'page_type': 'InternationalArticlePage',
            'meta': {
                'slug': 'foo',
                'languages': [('en-gb', 'English')],
            },
        }
    )
    response = client.get(url)

    breadcrumbs = response.context_data['breadcrumbs']
    assert breadcrumbs == [
        {
            'url': '/international/',
            'label': 'International'
        },
        {
            'url': '/international/bar/',
            'label': 'Bar'
        },
        {
            'url': '/international/bar/foo/',
            'label': 'Foo'
        },
    ]


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_article_detail_page_social_share_links(
    mock_get_page, client, settings
):

    test_article_page = {
        'title': 'Test article admin title',
        'article_title': 'Test article',
        'article_image': {'url': 'foobar.png'},
        'article_body_text': '<p>Lorem ipsum</p>',
        'related_pages': [],
        'full_path': (
            '/international/bar/foo/'),
        'last_published_at': '2018-10-09T16:25:13.142357Z',
        'meta': {
            'slug': 'foo',
            'languages': [('en-gb', 'English')],
        },
        'page_type': 'InternationalArticlePage',
    }

    url = reverse('article-detail', kwargs={'list': 'bar', 'slug': 'foo'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload=test_article_page
    )

    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    assert response.status_code == 200
    assert response.template_name == ['core/article_detail.html']

    twitter_link = (
        'https://twitter.com/intent/tweet?text=great.gov.uk'
        '%20-%20Test%20article%20'
        'http://testserver/international/bar/foo/')
    facebook_link = (
        'https://www.facebook.com/share.php?u=http://testserver/'
        'international/bar/foo/')
    linkedin_link = (
        'https://www.linkedin.com/shareArticle?mini=true&url='
        'http://testserver/international/bar/foo/&title=great.gov.uk'
        '%20-%20Test%20article%20&source=LinkedIn'
    )
    email_link = (
        'mailto:?body=http://testserver/international/bar/'
        'foo/&subject=great.gov.uk%20-%20Test%20article%20'
    )

    assert soup.find(id='share-twitter').attrs['href'] == twitter_link
    assert soup.find(id='share-facebook').attrs['href'] == facebook_link
    assert soup.find(id='share-linkedin').attrs['href'] == linkedin_link
    assert soup.find(id='share-email').attrs['href'] == email_link


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_article_detail_page_social_share_links_no_title(
    mock_get_page, client, settings
):

    test_article_page = {
        'title': 'Test article admin title',
        'article_image': {'url': 'foobar.png'},
        'article_body_text': '<p>Lorem ipsum</p>',
        'related_pages': [],
        'full_path': (
            '/international/bar/foo/'),
        'last_published_at': '2018-10-09T16:25:13.142357Z',
        'meta': {
            'slug': 'foo',
            'languages': [('en-gb', 'English')],
        },
        'page_type': 'InternationalArticlePage',
    }

    url = reverse('article-detail', kwargs={'list': 'bar', 'slug': 'foo'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload=test_article_page
    )

    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    assert response.status_code == 200
    assert response.template_name == ['core/article_detail.html']

    twitter_link = (
        'https://twitter.com/intent/tweet?text=great.gov.uk%20-%20%20'
        'http://testserver/international/bar/foo/'
        '')
    linkedin_link = (
        'https://www.linkedin.com/shareArticle?mini=true&url='
        'http://testserver/international/bar/foo/'
        '&title=great.gov.uk'
        '%20-%20%20&source=LinkedIn'
    )
    email_link = (
        'mailto:?body=http://testserver/international/bar/'
        'foo/&subject='
        'great.gov.uk%20-%20%20'
    )

    assert soup.find(id='share-twitter').attrs['href'] == twitter_link
    assert soup.find(id='share-linkedin').attrs['href'] == linkedin_link
    assert soup.find(id='share-email').attrs['href'] == email_link


campaign_page_all_fields = {
    'campaign_heading': 'Campaign heading',
    'campaign_hero_image': {'url': 'campaign_hero_image.jpg'},
    'cta_box_button_text': 'CTA box button text',
    'cta_box_button_url': '/cta_box_button_url',
    'cta_box_message': 'CTA box message',
    'related_content_heading': 'Related content heading',
    'related_content_intro': '<p>Related content intro.</p>',
    'section_one_contact_button_text': 'Section one contact button text',
    'section_one_contact_button_url': '/section_one_contact_button_url',
    'section_one_heading': 'Section one heading',
    'section_one_image': {'url': 'section_one_image.jpg'},
    'section_one_intro': '<p>Section one intro.</p>',
    'section_two_contact_button_text': 'Section one contact button text',
    'section_two_contact_button_url': '/section_two_contact_button_url',
    'section_two_heading': 'Section two heading',
    'section_two_image': {'url': 'section_two_image.jpg'},
    'section_two_intro': '<p>Section two intro</p>',
    'selling_point_one_content': '<p>Selling point one content</p>',
    'selling_point_one_heading': 'Selling point one heading',
    'selling_point_one_icon': {'url': 'selling_point_one_icon.jpg'},
    'selling_point_two_content': '<p>Selling point two content</p>',
    'selling_point_two_heading': 'Selling point two heading',
    'selling_point_two_icon': {'url': 'selling_point_two_icon.jpg'},
    'selling_point_three_content': '<p>Selling point three content</p>',
    'selling_point_three_heading': 'Selling point three heading',
    'selling_point_three_icon': {'url': 'selling_point_three_icon.jpg'},
    'related_pages': [
        {
            'article_image': {'url': 'article_image.jpg'},
            'article_image_thumbnail': {'url': 'article1_image_thumbnail.jpg'},
            'article_teaser': 'Related article description 1',
            'article_title': 'Related article 1',
            'full_path': '/advice/finance/article-1/',
            'meta': {
                'languages': [['en-gb', 'English']],
                'slug': 'article-1'},
            'page_type': 'InternationalArticlePage',
            'title': 'Related article 1'
        },
        {
            'article_image': {'url': 'article_image.jpg'},
            'article_image_thumbnail': {'url': 'article2_image_thumbnail.jpg'},
            'article_teaser': 'Related article description 2',
            'article_title': 'Related article 2',
            'full_path': '/advice/finance/article-2/',
            'meta': {
                'languages': [['en-gb', 'English']],
                'slug': 'article-2'},
            'page_type': 'InternationalArticlePage',
            'title': 'Related article 2'
        },
        {
            'article_image': {'url': 'article_image.jpg'},
            'article_image_thumbnail': {'url': 'article3_image_thumbnail.jpg'},
            'article_teaser': 'Related article description 3',
            'article_title': 'Related article 3',
            'full_path': '/advice/finance/article-3/',
            'meta': {
                'languages': [('en-gb', 'English')],
                'slug': 'article-3'},
            'page_type': 'InternationalArticlePage',
            'title': 'Related article 3'
        },
    ],
    'meta': {
        'languages': [('en-gb', 'English')],
        'slug': 'test-page'
    },
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_marketing_campaign_campaign_page_all_fields(
    mock_get_page, client, settings
):
    url = reverse('campaign', kwargs={'slug': 'test-page'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload=campaign_page_all_fields
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['core/campaign.html']

    soup = BeautifulSoup(response.content, 'html.parser')

    assert ('<p class="body-text">Selling point two content</p>'
            ) in str(response.content)

    assert ('<p class="body-text">Selling point three content</p>'
            ) in str(response.content)

    hero_section = soup.find(id='campaign-hero')

    exp_style = "background-image: url('{}')".format(
        campaign_page_all_fields['campaign_hero_image']['url'])

    assert hero_section.attrs['style'] == exp_style

    assert soup.find(
        id='selling-points-icon-two').attrs['src'] == campaign_page_all_fields[
        'selling_point_two_icon']['url']

    assert soup.find(
        id='selling-points-icon-three'
    ).attrs['src'] == campaign_page_all_fields[
        'selling_point_three_icon']['url']

    assert soup.find(
        id='section-one-contact-button'
    ).attrs['href'] == campaign_page_all_fields[
        'section_one_contact_button_url']
    assert soup.find(
        id='section-one-contact-button').text == campaign_page_all_fields[
        'section_one_contact_button_text']

    assert soup.find(
        id='section-two-contact-button'
    ).attrs['href'] == campaign_page_all_fields[
        'section_two_contact_button_url']
    assert soup.find(
        id='section-two-contact-button').text == campaign_page_all_fields[
        'section_two_contact_button_text']

    related_page_one = soup.find(id='related-page-article-1')
    assert related_page_one.find('a').text == 'Related article 1'
    assert related_page_one.find('p').text == 'Related article description 1'
    assert related_page_one.find('a').attrs['href'] == (
        '/advice/finance/article-1/')
    assert related_page_one.find('img').attrs['src'] == (
        'article1_image_thumbnail.jpg')

    related_page_two = soup.find(id='related-page-article-2')
    assert related_page_two.find('a').text == 'Related article 2'
    assert related_page_two.find('p').text == 'Related article description 2'
    assert related_page_two.find('a').attrs['href'] == (
        '/advice/finance/article-2/')
    assert related_page_two.find('img').attrs['src'] == (
        'article2_image_thumbnail.jpg')

    related_page_three = soup.find(id='related-page-article-3')
    assert related_page_three.find('a').text == 'Related article 3'
    assert related_page_three.find('p').text == 'Related article description 3'
    assert related_page_three.find('a').attrs['href'] == (
        '/advice/finance/article-3/')
    assert related_page_three.find('img').attrs['src'] == (
        'article3_image_thumbnail.jpg')


campaign_page_required_fields = {
    'campaign_heading': 'Campaign heading',
    'campaign_hero_image': None,
    'cta_box_button_text': 'CTA box button text',
    'cta_box_button_url': '/cta_box_button_url',
    'cta_box_message': 'CTA box message',
    'related_content_heading': 'Related content heading',
    'related_content_intro': '<p>Related content intro.</p>',
    'related_pages': [],
    'section_one_contact_button_text': None,
    'section_one_contact_button_url': None,
    'section_one_heading': 'Section one heading',
    'section_one_image': None,
    'section_one_intro': '<p>Section one intro.</p>',
    'section_two_contact_button_text': None,
    'section_two_contact_button_url': None,
    'section_two_heading': 'Section two heading',
    'section_two_image': None,
    'section_two_intro': '<p>Section two intro</p>',
    'selling_point_one_content': '<p>Selling point one content</p>',
    'selling_point_one_heading': 'Selling point one heading',
    'selling_point_one_icon': None,
    'selling_point_two_content': '<p>Selling point two content</p>',
    'selling_point_two_heading': 'Selling point two heading',
    'selling_point_two_icon': None,
    'selling_point_three_content': '<p>Selling point three content</p>',
    'selling_point_three_heading': 'Selling point three heading',
    'selling_point_three_icon': None,
    'meta': {
        'languages': [('en-gb', 'English')],
        'slug': 'test-page'
    },
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_marketing_campaign_page_required_fields(
    mock_get_page, client, settings
):
    url = reverse('campaign', kwargs={'slug': 'test-page'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload=campaign_page_required_fields
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['core/campaign.html']

    soup = BeautifulSoup(response.content, 'html.parser')

    assert ('<p class="body-text">Selling point two content</p>'
            ) in str(response.content)

    assert ('<p class="body-text">Selling point three content</p>'
            ) in str(response.content)

    hero_section = soup.find(id='campaign-hero')
    assert not hero_section.attrs.get('style')

    assert not soup.find(id='selling-points-icon-two')
    assert not soup.find(id='selling-points-icon-three')

    assert not soup.find(id='section-one-contact-button')
    assert not soup.find(id='section-one-contact-button')

    assert not soup.find(id='section-two-contact-button')
    assert not soup.find(id='section-two-contact-button')

    assert soup.select(
        '#campaign-contact-box .box-heading'
        )[0].text == campaign_page_required_fields['cta_box_message']

    assert soup.find(
        id='campaign-hero-heading'
        ).text == campaign_page_required_fields['campaign_heading']

    assert soup.find(
        id='section-one-heading'
        ).text == campaign_page_required_fields['section_one_heading']

    assert soup.find(
        id='section-two-heading'
        ).text == campaign_page_required_fields['section_two_heading']

    assert soup.find(
        id='related-content-heading'
        ).text == campaign_page_required_fields['related_content_heading']

    assert soup.select(
        "li[aria-current='page']"
        )[0].text == campaign_page_required_fields['campaign_heading']


test_articles = [
    {
        'seo_title': 'SEO title article 1',
        'search_description': 'Search description article 1',
        'article_title': 'Article 1 title',
        'article_teaser': 'Article 1 teaser.',
        'article_image': {'url': 'article_image1.png'},
        'article_body_text': '<p>Lorem ipsum 1</p>',
        'last_published_at': '2018-10-01T15:16:30.583279Z',
        'full_path': '/topic/list/article-one/',
        'tags': [
            {'name': 'Test tag', 'slug': 'test-tag'},
        ],
        'meta': {'slug': 'article-one'}
    },
    {
        'seo_title': 'SEO title article 2',
        'search_description': 'Search description article 2',
        'article_title': 'Article 2 title',
        'article_teaser': 'Article 2 teaser.',
        'article_image': {'url': 'article_image2.png'},
        'article_body_text': '<p>Lorem ipsum 2</p>',
        'last_published_at': '2018-10-02T15:16:30.583279Z',
        'full_path': '/topic/list/article-two/',
        'tags': [
            {'name': 'Test tag', 'slug': 'test-tag'},
        ],
        'meta': {'slug': 'article-two'}
    },
]

test_list_page = {
    'title': 'List CMS admin title',
    'seo_title': 'SEO title article list',
    'search_description': 'Article list search description',
    'landing_page_title': 'Article list landing page title',
    'hero_image': {'url': 'article_list.png'},
    'hero_teaser': 'Article list hero teaser',
    'list_teaser': '<p>Article list teaser</p>',
    'articles': test_articles,
    'page_type': 'InternationalArticleListingPage',
    'meta': {
        'slug': 'article-list',
        'languages': [('en-gb', 'English')],
    },
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_article_list_page(mock_get_page, client, settings):

    url = reverse('article-list', kwargs={'slug': 'article-list'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_payload=test_list_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['core/article_list.html']

    assert test_list_page['title'] not in str(response.content)
    assert test_list_page['landing_page_title'] in str(response.content)

    assert '01 October' in str(response.content)
    assert '02 October' in str(response.content)
