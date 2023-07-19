import math
import re
import requests
import cloudscraper
from bs4 import BeautifulSoup
from html2text import html2text

"""classes:
Pagination
Work + WorkPagination
User + UserPagination
Pseud + PseudPagination (user/{name}/pseuds)
Tag + 
Comment
Search
"""

"""planning:

-PHASE 1: work, tags, work search, user/pseud metadata
-PHASE 2: chapters, read comments, caching
-PHASE 3: intractability: comments, kudos, etc.

"""

baseURL = "https://archiveofourown.org"


class Unloaded:
    pass


def request(url):
    # r = cloudscraper.CloudScraper().get(url)
    if not isinstance(url, str):
        raise Exception("URL must be string")
    else:
        print("REQUEST: "+url)
        r = requests.get(url)
        print("STATUS: "+str(r.status_code))
        return r

def _format_text(text):
    if text is None:
        return None
    return "".join(
        [s for s in html2text(
            html=str(text).replace("<blockquote", "<div").replace("</blockquote", "</div"),
            bodywidth=0
        ).splitlines(True) if s.strip("\r\n")]
    ).strip()

class AO3Item:
    def _check_property(self, prop, load=None):
        if type(prop) is Unloaded:
            if load is None:
                self.load()
            else:
                load()

    def load(self):
        pass


class AO3Exception(Exception):
    pass


class Pagination:
    # TODO: should be private variables
    # TODO: implement slice method _getslice_
    url = Unloaded()
    items = Unloaded()
    page_size = Unloaded()
    _item_selector = Unloaded()

    def __init__(self, url, page_size, item_count):
        self.items = [None for i in range(item_count)]
        self.url = url
        self.page_size = page_size

    def __setitem__(self, index, item):
        print("CHANGE THIS TO CALL items DIRECTLY")
        self.items[index] = item

    def __getitem__(self, index):
        item = self.items[index]
        return self.fetch(index) if item is None else item

    def __len__(self):
        return len(self.items)

    def to_list(self):  # only returns works that have been loaded into memory
        return [item for item in self.items if item is not None]

    def fetch(self, index):
        pass


class WorkPagination(Pagination):
    _item_selector = ":not(.userstuff) li.work"

    def fetch(self, index):
        page = math.floor(index / self.page_size) + 1
        page_item = index % self.page_size

        url = self.url
        if '?' in url:
            url += f"&page={page}"
        else:
            url += f"?page={page}"
        print("> WorkPagination:load")
        r = request(f'{url}')
        if r.status_code != 200:
            raise AO3Exception("Resource not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        elms = soup.select(self._item_selector)
        start = (page - 1) * self.page_size
        for i in range(0, len(elms)):
            self.items[start + i] = Work.parse_listing(elms[i])
        return self.items[index]


class Pseud(AO3Item):
    _name = Unloaded()
    _pseud = Unloaded()
    _main = Unloaded()
    _url = Unloaded()
    _pfp = Unloaded()  # url to profile picture
    _pfp_alt_text = Unloaded()
    _works = Unloaded()
    _soup = Unloaded()
    """ TODO:
    _fandoms = Unloaded()
    _series = Unloaded()
    _bookmarks = Unloaded()
    _collections = Unloaded()
    _gifts = Unloaded()
    _description = Unloaded()  # from ../users/{name}/pseuds page
    """

    def __init__(self, name=None, pseud=None):
        if name is None or (name is None and pseud is None):
            return

        if pseud == "orphan_account":
            pseud = None
        self._name = name
        self._pseud = pseud
        self.load()

    @staticmethod
    def parse_listing(soup):
        pseud = Pseud()
        pseud._url = f'{baseURL}{soup.get("href")}'
        if ' ' in soup.text.strip():  # is pseud work
            names = soup.text.strip()[:-1].split(' (')
            pseud._pseud = names[0]
            pseud._name = names[1]
        else:
            name = soup.text.strip()
            pseud._name = name
            pseud._pseud = name
        return pseud

    def load(self):
        if self._name is None:
            raise Exception("'name' field is unset")
        self._url = f'{baseURL}/users/{self._name}/' + ('' if self._pseud is None else f'pseuds/{self._pseud}/')
        print("> Pseud:load")
        r = request(self._url)
        if r.status_code != 200 or "people/search" in r.url:
            raise AO3Exception("User or Pseud not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        self._soup = soup

        work_count = int(re.sub(
            r'[^0-9]',
            '',
            soup.select(':not(.userstuff)#dashboard ul.navigation.actions')[1].select("li")[0].text
        ))
        self._works = WorkPagination(f"{self._url}works", 20, work_count)
        elms = soup.select(":not(.userstuff) li.work")
        for i in range(0, len(elms)):
            self._works.items[i] = Work.parse_listing(elms[i])
        pfp = soup.select_one(':not(.userstuff).icon a img')
        if "s3.amazonaws.com" in str(pfp):
            self._pfp = pfp.get('src')
            self._pfp_alt_text = pfp.get('alt')
        else:
            self._pfp = baseURL + '/images/skins/iconsets/default/icon_user.png'
            self._pfp_alt_text = ""

    @property
    def name(self):
        super()._check_property(self._name)
        return self._name

    @property
    def pseud(self):
        super()._check_property(self._pseud)
        return self._pseud

    @property
    def main(self):
        super()._check_property(self._main)
        return self._main

    @property
    def url(self):
        super()._check_property(self._url)
        return self._url

    @property
    def pfp(self):
        super()._check_property(self._pfp)
        return self._pfp

    @property
    def pfp_alt_text(self):
        super()._check_property(self._pfp_alt_text)
        return self._pfp_alt_text

    @property
    def works(self):
        super()._check_property(self._works)
        return self._works

    @property
    def soup(self):
        super()._check_property(self._soup)
        return self._soup


class User(Pseud):
    _pseuds = Unloaded()
    _collections = Unloaded()
    _gifts = Unloaded()
    # profile
    _has_parsed_profile = False
    _title = Unloaded()
    _join_date = Unloaded()
    _user_id = Unloaded()
    _location = Unloaded()
    _bio = Unloaded()

    """def __init__(self, name=None, pseud=None):
        if name is None:
            return
        self.name = name
        if pseud is not None:
            self.pseud = pseud
        self.load()

    def load(self):
        super().load()"""

    def load_profile(self):
        # TODO: load url/profile
        print("load url/profile")
        pass

    @property
    def title(self):
        super()._check_property(self._title, self.load_profile)
        return self._title

    @property
    def main(self):
        return self


class Work(AO3Item):
    _work_id = Unloaded()
    _title = Unloaded()
    _url = Unloaded()
    _last_chapter_url = Unloaded()
    _authors = Unloaded()
    _rating = Unloaded()
    _category = Unloaded()
    _archive_warnings = Unloaded()
    _fandoms = Unloaded()
    _relationships = Unloaded()
    _characters = Unloaded()
    _tags = Unloaded()
    _summary = Unloaded()
    _start_notes = Unloaded()
    _end_notes = Unloaded()
    _language = Unloaded()
    _published = Unloaded()
    _updated = Unloaded()
    _words = Unloaded()
    _chapter_count = Unloaded()
    _chapter_max = Unloaded()
    _comment_count = Unloaded()
    _kudos = Unloaded()
    _bookmarks = Unloaded()
    _hits = Unloaded()
    _chapters = Unloaded()
    _comments = "WIP"
    _soup = Unloaded()

    def __init__(self, work_id=None, load_all_chapters=False):
        if work_id is None:
            return
        self._work_id = work_id
        self._url = f'{baseURL}/works/{work_id}?view_adult=true&show_comments=true{"&view_full_work=true" * load_all_chapters}'
        self.load()

    def load(self, url=None):
        if url is None:
            url = self._url
            if url is Unloaded:
                raise Exception("Work URL must be set internally before a work can be loaded.")
        print("> Work:load")
        r = request(url)
        if r.status_code != 200:
            raise AO3Exception("Work not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        self._soup = soup

        self._url = f'{baseURL}/works/{self._work_id}?view_comments=true'
        self._title = soup.select_one('#workskin .title.heading').text.strip()
        self._rating = soup.select_one(':not(#workskin) dd.rating.tags a.tag').text.strip()
        self._category = soup.select_one(':not(#workskin) dd.category.tags a.tag').text.strip()
        self._authors = \
            [User.parse_listing(elm) for elm in soup.select('#workskin .preface.group .byline.heading a[rel=author]')]
        self._archive_warnings = \
            soup.select_one(':not(#workskin) dd.warning.tags .tag').text.strip().split(', ')
        self._fandoms = [Tag.parse_tag(elm) for elm in soup.select(':not(#workskin) dd.fandom.tags a.tag')]
        self._relationships = [Tag.parse_tag(elm) for elm in
                                soup.select(':not(#workskin) dd.relationship.tags a.tag')]
        self._characters = [Tag.parse_tag(elm) for elm in soup.select(':not(#workskin) dd.character.tags a.tag')]
        self._tags = [Tag.parse_tag(elm) for elm in soup.select(':not(#workskin) dd.freeform.tags a.tag')]
        try:
            self._summary = _format_text(soup.select_one('#workskin .summary:not(.chapter) .userstuff'))
        except AttributeError:
            pass
        self._start_notes = _format_text(soup.select_one('#workskin .notes .userstuff'))
        self._language = soup.select_one(':not(#workskin) dd.language').text.strip()
        try:
            self._published = soup.select_one(':not(#workskin) dd.published').text.strip()
        except AttributeError:
            self._published = None
        try:
            self._updated = soup.select_one(':not(#workskin) dd.status').text.strip()
        except AttributeError:
            self._updated = None
        self._words = int(soup.select_one(':not(#workskin) .stats dd.words').text.strip().replace(',', ''))
        chapter_label = soup.select_one(":not(#workskin) .stats dd.chapters").text.strip().split('/')
        self._chapter_count = int(chapter_label[0].replace(',', ''))
        self._chapter_max = None if chapter_label[1] == '?' else int(chapter_label[1].replace(',', ''))
        try:
            self._comment_count = \
                int(soup.select_one(':not(#workskin) .stats dd.comments').text.strip().replace(',', ''))
        except AttributeError:
            self._comment_count = 0
        try:
            self._kudos = int(soup.select_one(':not(#workskin) .stats dd.kudos').text.strip().replace(',', ''))
        except AttributeError:
            self._kudos = 0
        try:
            self._bookmarks = int(soup.select_one(':not(#workskin) .stats dd.bookmarks').text.strip().replace(',', ''))
        except AttributeError:
            self._bookmarks = 0
        try:
            self._hits = int(soup.select_one(':not(#workskin) .stats dd.hits').text.strip().replace(',', ''))
        except AttributeError:
            self._hits = 0

        # TODO: self._comments = []
        self._chapters = [
            Chapter.parse_list_item(chapter, self) for chapter in soup.select(
                ":not(#workskin) li.chapter #selected_id option")
        ]

        # HACK: no chapter selector exists if only 1 chapter exists so we need a different way to get chap link and name
        if len(self._chapters) > 0:
            self._last_chapter_url = self._chapters[-1].url
        else:
            self._last_chapter_url = url

    def _load_end_notes(self):
        soup = self._chapters[-1].soup
        self._end_notes = _format_text(soup.select_one('#workskin .afterword .end.notes .userstuff'))

    @staticmethod
    def parse_listing(soup):
        work = Work()
        work._url = f"{baseURL}{soup.select_one(':not(.userstuff).header h4.heading a:not([ref=author])').get('href')}"
        work._work_id = Work.get_work_id_from_url(work._url)
        last_chapter_elm = soup.select_one(':not(.userstuff).stats dd.chapters a')
        work._last_chapter_url = work._url if last_chapter_elm is None else f"{baseURL}{last_chapter_elm.get('href')}"
        work._title = soup.select_one(':not(.userstuff).header h4.heading a:not([ref=author])').text.strip()
        work._rating = soup.select_one(':not(.userstuff).required-tags li .rating span').text.strip()
        work._category = soup.select_one(':not(.userstuff).required-tags li .category span').text.strip()
        work._authors = \
            [User.parse_listing(elm) for elm in soup.select(':not(.userstuff).header .heading a[rel=author]')]
        work._archive_warnings = \
            soup.select_one(':not(.userstuff).required-tags li .warnings span').text.strip().split(', ')
        work._fandoms = [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) .fandoms a.tag')]
        work._relationships = \
            [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) ul.tags li.relationships a')]
        work._characters = [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) ul.tags li.characters a')]
        work._tags = [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) ul.tags li.freeforms a')]
        try:
            work._summary = _format_text(soup.select_one('.userstuff.summary'))
        except AttributeError:
            pass
        work._language = soup.select_one(':not(.userstuff).stats dd.language').text.strip()
        work._words = int(soup.select_one(':not(.userstuff).stats dd.words').text.strip().replace(',', ''))
        chapters = soup.select_one(":not(.userstuff).stats dd.chapters").text.strip().split('/')
        work._chapter_count = int(chapters[0].replace(',', ''))
        work._chapter_max = None if chapters[1] == '?' else int(chapters[1].replace(',', ''))
        try:
            work._comment_count = \
                int(soup.select_one(':not(.userstuff).stats dd.comments').text.strip().replace(',', ''))
        except AttributeError:
            work._comment_count = 0
        try:
            work._kudos = int(soup.select_one(':not(.userstuff).stats dd.kudos').text.strip().replace(',', ''))
        except AttributeError:
            work._kudos = 0
        try:
            work._bookmarks = int(soup.select_one(':not(.userstuff).stats dd.bookmarks').text.strip().replace(',', ''))
        except AttributeError:
            work._bookmarks = 0
        try:
            work._hits = int(soup.select_one(':not(.userstuff).stats dd.hits').text.strip().replace(',', ''))
        except AttributeError:
            work._hits = 0
        return work

    @staticmethod
    def get_work_id_from_url(url):
        url_parts = url.split('/')
        for i, part in enumerate(url_parts):
            if part == "works":
                return url_parts[i + 1].split('?')[0]
        return None

    @staticmethod
    def search(
            query='',
            title='',
            creators='',
            revised_at='',
            complete='',  # '' = Any, T = Complete, F = WIP
            crossover='',  # '' = Any, T = Only Crossovers, F = No Crossovers
            single_chapter='0',  # ''/0 = Any Chapter Count, 1 = Single Chapter Only
            word_count='',
            language_id='',
            fandom_names='',
            rating_ids='',
            character_names='',
            relationship_names='',
            freeform_names='',
            hits='',
            kudos_count='',
            comments_count='',
            bookmarks_count='',
            sort_column='_score',
            sort_direction='desc'):
        """
        *: any characters
            book* will find book and books and booking.
        space: acts like AND for search terms in the same field of the work
            Harry Potter will find Harry Potter and Harry James Potter in any field, but it won't find works by a
            creator named Harry with the character tag Sherman Potter.
        AND: searches for works which have both terms in any field
            Harry AND Potter will find works by a creator named Harry with the character tag Sherman Potter.
        ||: OR (not exclusive)
            Harry || Potter will find Harry, Harry Potter, and Potter.
        "": words in exact sequence
            "Harry Lockhart" will find Harry Lockhart but not Harry Potter/Gilderoy Lockhart.
        -: NOT
            Harry -Lockhart will find Harry Potter but not Harry Lockhart or Gilderoy Lockhart/Harry Potter.

        """
        params = {
            "query": query,
            "title": title,
            "creators": creators,
            "revised_at": revised_at,
            "complete": complete,
            "crossover": crossover,
            "single_chapter": single_chapter,
            "word_count": word_count,
            "language_id": language_id,
            "fandom_names": fandom_names,
            "rating_ids": rating_ids,
            "character_names": character_names,
            "relationship_names": relationship_names,
            "freeform_names": freeform_names,
            "hits": hits,
            "kudos_count": kudos_count,
            "comments_count": comments_count,
            "bookmarks_count": bookmarks_count,
            "sort_column": sort_column,
            "sort_direction": sort_direction,
        }
        url = f'{baseURL}/works/search?commit=Search&work_search['
        url += "&work_search[".join([f"{param}]={params[param]}" for param in params.keys()])
        print("> Work:search")
        r = request(url)
        if r.status_code != 200:
            raise AO3Exception("No works not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        work_count = 0
        try:
            work_count = int(soup.select("#main .heading")[2].text.split(' ')[0].replace(',', ''))
        except IndexError:
            return []

        works = WorkPagination(f"{url}", 20, work_count)
        elms = soup.select(":not(.userstuff) li.work")
        for i in range(0, len(elms)):
            works.items[i] = Work.parse_listing(elms[i])
        return works

    @property
    def work_id(self):
        super()._check_property(self._work_id)
        return self._work_id

    @property
    def title(self):
        super()._check_property(self._title)
        return self._title

    @property
    def url(self):
        super()._check_property(self._url)
        return self._url

    @property
    def authors(self):
        super()._check_property(self._authors)
        return self._authors

    @property
    def rating(self):
        super()._check_property(self._rating)
        return self._rating

    @property
    def archive_warnings(self):
        super()._check_property(self._archive_warnings)
        return self._archive_warnings

    @property
    def fandoms(self):
        super()._check_property(self._fandoms)
        return self._fandoms

    @property
    def relationships(self):
        super()._check_property(self._relationships)
        return self._relationships

    @property
    def characters(self):
        super()._check_property(self._characters)
        return self._characters

    @property
    def tags(self):
        super()._check_property(self._tags)
        return self._tags

    @property
    def summary(self):
        super()._check_property(self._summary)
        return self._summary

    @property
    def start_notes(self):
        super()._check_property(self._start_notes)
        return self._start_notes

    @property
    def end_notes(self):
        super()._check_property(self._end_notes, self._load_end_notes)
        return self._end_notes

    @property
    def language(self):
        super()._check_property(self._language)
        return self._language

    @property
    def published(self):
        super()._check_property(self._published)
        return self._published

    @property
    def updated(self):
        super()._check_property(self._updated)
        return self._updated

    @property
    def words(self):
        super()._check_property(self._words)
        return self._words

    @property
    def chapter_count(self):
        super()._check_property(self._chapter_count)
        return self._chapter_count

    @property
    def chapter_max(self):
        super()._check_property(self._chapter_max)
        return self._chapter_max

    @property
    def comment_count(self):
        super()._check_property(self._comment_count)
        return self._comment_count

    @property
    def kudos(self):
        super()._check_property(self._kudos)
        return self._kudos

    @property
    def bookmarks(self):
        super()._check_property(self._bookmarks)
        return self._bookmarks

    @property
    def hits(self):
        super()._check_property(self._hits)
        return self._hits

    @property
    def chapters(self):
        super()._check_property(self._chapters)
        return self._chapters

    @property
    def soup(self):
        super()._check_property(self._soup)
        return self._soup


class Chapter(AO3Item):
    _name = Unloaded()
    _chapter_id = Unloaded()
    _url = Unloaded()
    _number = Unloaded()
    _summary = Unloaded()
    _start_notes = Unloaded()
    _end_notes = Unloaded()
    _content = Unloaded()  # the text of a chapter converted to markdown, do conversion on demand and store to save cpu
    _content_html = Unloaded()  # the original chapter html
    # reference to parent work
    _work = Unloaded()
    _soup = Unloaded()

    def __init__(self, chapter_id=None, work=None):
        print("init chapter")
        print((chapter_id, work))
        if work is None and chapter_id is None:  # no source provided, skip
            return
        elif chapter_id is None:  # parse based on current work soup
            self._url = work._url
            self._id = None
            self.load(work.soup, work)
        else:
            print("load from chapter id")
            self._url = f'{baseURL}/chapters/{chapter_id}?view_adult=true&show_comments=true'
            self._id = chapter_id
            self.load(None, work)

    def load(self, soup=None, work=None):
        if soup is None:
            print("> Chapter:load")
            r = request(self._url)
            if r.status_code != 200:
                raise AO3Exception("Chapter not found.")
            soup = BeautifulSoup(r.text, 'lxml')
        self._soup = soup
        name_parts = soup.select_one("#workskin .chapter .title").text.strip().split(' ')
        self._name = ' '.join(name_parts[:2]) if len(name_parts) == 2 else ' '.join(name_parts[2:])
        self._number = name_parts[1].replace(':', '')
        self._summary = _format_text(soup.select_one("#workskin .chapter.preface .summary .userstuff"))
        self._start_notes = _format_text(soup.select_one("#workskin .preface .notes:not(.end) .userstuff"))
        self._end_notes = _format_text(soup.select_one("#workskin .preface .end.notes .userstuff"))
        self._content = None  # TODO: the text of a chapter converted to markdown
        self._content_html = None  # TODO: the original chapter html
        if work:
            self._work = work
        else:
            work = Work()
            work._url = baseURL \
                         + soup.select_one(":not(#workskin) li.chapter.entire a").get("href").split('?')[0] \
                         + "?view_adult=true&show_comments=true"
            work._work_id = Work.get_work_id_from_url(work.url)
            self._work = work

    @staticmethod
    def parse_list_item(soup, work):
        chapter = Chapter()
        parts = soup.text.strip().split(' ')
        chapter._name = ' '.join(parts[1:])
        chapter._url = f'{baseURL}/chapters/{soup.get("value")}'
        chapter._number = parts[0][:-1]
        if work:
            chapter._work = work
        return chapter

    @staticmethod
    def get_chapter_id_from_url(url):
        url_parts = url.split('/')
        for i, part in enumerate(url_parts):
            if part == "chapters":
                return url_parts[i + 1].split('?')[0]
        return None

    @property
    def name(self):
        super()._check_property(self._name)
        return self._name

    @property
    def id(self):
        super()._check_property(self._id)
        return self._id

    @property
    def url(self):
        super()._check_property(self._url)
        return self._url

    @property
    def number(self):
        super()._check_property(self._number)
        return self._number

    @property
    def summary(self):
        super()._check_property(self._summary)
        return self._summary

    @property
    def start_notes(self):
        super()._check_property(self._start_notes)
        return self._start_notes

    @property
    def end_notes(self):
        super()._check_property(self._end_notes)
        return self._end_notes

    @property
    def content(self):
        super()._check_property(self._content)
        return self._content

    @property
    def content_html(self):
        super()._check_property(self._content_html)
        return self._content_html

    @property
    def work(self):
        super()._check_property(self._work)
        return self._work

    @property
    def soup(self):
        super()._check_property(self._soup)
        return self._soup


class Tag(AO3Item):
    _name = Unloaded()
    _url = Unloaded()
    _type = Unloaded()
    _canonized = Unloaded()
    _parents = Unloaded()
    _synonyms = Unloaded()
    _mergers = Unloaded()
    _meta = Unloaded()
    _characters = Unloaded()
    _relationships = Unloaded()
    _tags = Unloaded()
    _works = Unloaded()
    _soup = Unloaded()

    def load(self):
        print("> Tag:load")
        r = request(f"{baseURL}/tags/{self.name.replace('/', '*s*')}/")
        if r.status_code != 200:
            raise AO3Exception("Tag not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        self._soup = soup
        self._url = f"{baseURL}/tags/{self.name.replace('/', '*s*').replace(' ', '%20')}/"
        self._name = soup.select_one('.header h2.heading').text.strip()
        desc = soup.select_one('.tag.home.profile p').text.strip()
        self._type = desc.split(' ')[5]
        self._canonized = "It's a common tag" in desc
        self._parents = [self.parse_tag(elm) for elm in soup.select('.parent.listbox ul li a.tag')]
        self._synonyms = [self.parse_tag(elm) for elm in soup.select('.synonym.listbox ul li a.tag')]
        self._mergers = [self.parse_tag(elm) for elm in soup.select('.merger.module ul li a.tag')]
        self._meta = [self.parse_tag(elm) for elm in soup.select('.meta.listbox a.tag')]
        self._characters = [self.parse_tag(elm) for elm in soup.select('.characters.listbox ul li a.tag')]
        self._relationships = [self.parse_tag(elm) for elm in soup.select('.relationships.listbox ul li a.tag')]
        self._tags = [self.parse_tag(elm) for elm in soup.select('.freeforms.listbox ul li a.tag')]

    def __init__(self, name=None):
        if name is None:
            return
        self._name = name
        self.load()

    @property
    def name(self):
        super()._check_property(self._name)
        return self._name

    @property
    def url(self):
        super()._check_property(self._url)
        return self._url

    @property
    def type(self):
        super()._check_property(self._type)
        return self._type

    @property
    def canonized(self):
        super()._check_property(self._canonized)
        return self._canonized

    @property
    def parents(self):
        super()._check_property(self._parents)
        return self._parents

    @property
    def synonyms(self):
        super()._check_property(self._synonyms)
        return self._synonyms

    @property
    def meta(self):
        super()._check_property(self._meta)
        return self._meta

    @property
    def characters(self):
        super()._check_property(self._characters)
        return self._characters

    @property
    def relationships(self):
        super()._check_property(self._relationships)
        return self._relationships

    @property
    def tags(self):
        super()._check_property(self._tags)
        return self._tags

    @property
    def soup(self):
        super()._check_property(self._soup)
        return self._soup

    @property
    def works(self):
        if self._works is None:
            print("> Tag:works")
            r = request(f'{self._url}/works')
            if r.status_code != 200:
                raise AO3Exception("Unable to find works for this tag.")
            self.soup = BeautifulSoup(r.text, 'lxml')
            soup = self.soup
            work_count = \
                int(soup.select_one(":not(userstuff) h2.heading").text.strip().split(' ')[4].replace(",", "")) \
                    if soup.select_one(":not(userstuff).pagination") \
                    else int(soup.select_one(":not(userstuff) h2.heading").text.strip().split(' ')[0])
            self._works = WorkPagination(f"{self._url}/works", 20, work_count)
        return self._works

    @staticmethod
    def parse_tag(soup):
        tag = Tag()
        tag._name = soup.text.strip()
        tag._url = f"{baseURL}/tags/{tag._name.replace('/', '*s*').replace(' ', '%20')}/"
        if tag._url[-6:] == "/works":  # links inconsistently append /works
            tag._url = tag._url[:-6]

        return tag
