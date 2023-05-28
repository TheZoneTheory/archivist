import math
import re
import requests
from bs4 import BeautifulSoup
from html2text import html2text

baseURL = "https://archiveofourown.org"

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

-PHASE 1: tags, works, users
-PHASE 2: work search, tag search
-PHASE 3: comments
-PHASE 4: people search, bookmark search

"""


class Unloaded:
    pass


class AO3Item:
    def _check_property(self, prop, load=None):
        if type(prop) is Unloaded:
            if load is None:
                self.load()
            else:
                load()

    def load(self):
        pass

    @staticmethod
    def _format_text(text):
        if text is None:
            return None
        return "".join(
            [s for s in html2text(
                html=str(text).replace("<blockquote", "<div").replace("</blockquote", "</div"),
                bodywidth=0
            ).splitlines(True) if s.strip("\r\n")]
        ).strip()


class AO3Exception(Exception):
    pass


class Pagination:
    # TODO: should be private variables
    # TODO: implement slice method __getslice__
    url = Unloaded()
    items = Unloaded()
    page_size = Unloaded()
    __item_selector = Unloaded()

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
    __item_selector = ":not(.userstuff) li.work"

    def fetch(self, index):
        page = math.floor(index / self.page_size) + 1
        page_item = index % self.page_size

        url = self.url
        if '?' in url:
            url += f"&page={page}"
        else:
            url += f"?page={page}"

        r = requests.get(f'{url}')
        if r.status_code != 200:
            raise AO3Exception("Resource not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        elms = soup.select(self.__item_selector)
        start = (page - 1) * self.page_size
        for i in range(0, len(elms)):
            self.items[start + i] = Work.parse_listing(elms[i])
        return self.items[index]


class Pseud(AO3Item):
    __name = Unloaded()
    __pseud = Unloaded()
    __main = Unloaded()
    __url = Unloaded()
    __pfp = Unloaded()  # url to profile picture
    __pfp_alt_text = Unloaded()
    __works = Unloaded()
    """ TODO:
    __fandoms = Unloaded()
    __series = Unloaded()
    __bookmarks = Unloaded()
    __collections = Unloaded()
    __gifts = Unloaded()
    __description = Unloaded()  # from ../users/{name}/pseuds page
    """

    def __init__(self, name=None, pseud=None):
        if name is None or (name is None and pseud is None):
            return

        if pseud == "orphan_account":
            pseud = None
        self.__name = name
        self.__pseud = pseud
        self.load()

    @staticmethod
    def parse_listing(soup):
        pseud = Pseud()
        pseud.__url = f'{baseURL}{soup.get("href")}'
        if ' ' in soup.text.strip():  # is pseud work
            names = soup.text.strip()[:-1].split(' (')
            pseud.__pseud = names[0]
            pseud.__name = names[1]
        else:
            name = soup.text.strip()
            pseud.__name = name
            pseud.__pseud = name
        return pseud

    def load(self):
        if self.__name is None:
            raise Exception("'name' field is unset")
        self.__url = f'{baseURL}/users/{self.__name}/' + ('' if self.__pseud is None else f'pseuds/{self.__pseud}/')
        r = requests.get(self.__url)
        if r.status_code != 200 or "people/search" in r.url:
            raise AO3Exception("User or Pseud not found.")
        soup = BeautifulSoup(r.text, 'lxml')

        work_count = int(re.sub(
            r'[^0-9]',
            '',
            soup.select(':not(.userstuff)#dashboard ul.navigation.actions')[1].select("li")[0].text
        ))
        self.__works = WorkPagination(f"{self.__url}works", 20, work_count)
        elms = soup.select(":not(.userstuff) li.work")
        for i in range(0, len(elms)):
            self.__works.items[i] = Work.parse_listing(elms[i])
        pfp = soup.select_one(':not(.userstuff).icon a img')
        self.__pfp = pfp.get('src')
        self.__pfp_alt_text = pfp.get('alt')

    @property
    def name(self):
        super()._check_property(self.__name)
        return self.__name

    @property
    def pseud(self):
        super()._check_property(self.__pseud)
        return self.__pseud

    @property
    def main(self):
        super()._check_property(self.__main)
        return self.__main

    @property
    def url(self):
        super()._check_property(self.__url)
        return self.__url

    @property
    def pfp(self):
        super()._check_property(self.__pfp)
        return self.__pfp

    @property
    def pfp_alt_text(self):
        super()._check_property(self.__pfp_alt_text)
        return self.__pfp_alt_text

    @property
    def works(self):
        super()._check_property(self.__works)
        return self.__works


class User(Pseud):
    __pseuds = Unloaded()
    __collections = Unloaded()
    __gifts = Unloaded()
    # profile
    __has_parsed_profile = False
    __title = Unloaded()
    __join_date = Unloaded()
    __user_id = Unloaded()
    __location = Unloaded()
    __bio = Unloaded()

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
        super()._check_property(self.__title, self.load_profile)
        return self.__title

    @property
    def main(self):
        return self


class Work(AO3Item):
    __work_id = Unloaded()
    __title = Unloaded()
    __url = Unloaded()
    __last_chapter_url = Unloaded()
    __authors = Unloaded()
    __rating = Unloaded()
    __category = Unloaded()
    __archive_warnings = Unloaded()
    __fandoms = Unloaded()
    __relationships = Unloaded()
    __characters = Unloaded()
    __tags = Unloaded()
    __summary = Unloaded()
    __start_notes = Unloaded()
    __end_notes = Unloaded()
    __language = Unloaded()
    __published = Unloaded()
    __updated = Unloaded()
    __words = Unloaded()
    __chapter_count = Unloaded()
    __chapter_max = Unloaded()
    __comment_count = Unloaded()
    __kudos = Unloaded()
    __bookmarks = Unloaded()
    __hits = Unloaded()
    __chapters = Unloaded()
    __comments = "WIP"

    def __init__(self, work_id=None, load_all_chapters=False):
        if work_id is None:
            return
        self.__work_id = work_id
        self.__url = f'{baseURL}/works/{work_id}?show_comments=true{"&view_full_work=true" * load_all_chapters}'
        self.load()

    def load(self, url=None):
        if url is None:
            url = self.__url
        r = requests.get(url)
        if r.status_code != 200:
            raise AO3Exception("Work not found.")
        soup = BeautifulSoup(r.text, 'lxml')

        self.__url = f'{baseURL}/works/{self.__work_id}?view_comments=true'
        self.__title = soup.select_one('#workskin .title.heading').text.strip()
        self.__rating = soup.select_one(':not(#workskin) dd.rating.tags a.tag').text.strip()
        self.__category = soup.select_one(':not(#workskin) dd.category.tags a.tag').text.strip()
        self.__authors = \
            [User.parse_listing(elm) for elm in soup.select('#workskin .preface.group .byline.heading a[rel=author]')]
        self.__archive_warnings = \
            soup.select_one(':not(#workskin) dd.warning.tags .tag').text.strip().split(', ')
        self.__fandoms = [Tag.parse_tag(elm) for elm in soup.select(':not(#workskin) dd.fandom.tags a.tag')]
        self.__relationships = [Tag.parse_tag(elm) for elm in
                                soup.select(':not(#workskin) dd.relationship.tags a.tag')]
        self.__characters = [Tag.parse_tag(elm) for elm in soup.select(':not(#workskin) dd.character.tags a.tag')]
        self.__tags = [Tag.parse_tag(elm) for elm in soup.select(':not(#workskin) dd.freeform.tags a.tag')]
        try:
            self.__summary = self._format_text(soup.select_one('#workskin .summary .userstuff'))
        except AttributeError:
            pass
        self.__start_notes = self._format_text(soup.select_one('#workskin .notes .userstuff'))
        self.__language = soup.select_one(':not(#workskin) dd.language').text.strip()
        try:
            self.__published = soup.select_one(':not(#workskin) dd.published').text.strip()
        except AttributeError:
            self.__published = None
        try:
            self.__updated = soup.select_one(':not(#workskin) dd.status').text.strip()
        except AttributeError:
            self.__updated = None
        self.__words = int(soup.select_one(':not(#workskin) .stats dd.words').text.strip().replace(',', ''))
        chapter_label = soup.select_one(":not(#workskin) .stats dd.chapters").text.strip().split('/')
        self.__chapter_count = int(chapter_label[0].replace(',', ''))
        self.__chapter_max = None if chapter_label[1] == '?' else int(chapter_label[1].replace(',', ''))
        try:
            self.__comment_count = \
                int(soup.select_one(':not(#workskin) .stats dd.comments').text.strip().replace(',', ''))
        except AttributeError:
            self.__comment_count = 0
        try:
            self.__kudos = int(soup.select_one(':not(#workskin) .stats dd.kudos').text.strip().replace(',', ''))
        except AttributeError:
            self.__kudos = 0
        try:
            self.__bookmarks = int(soup.select_one(':not(#workskin) .stats dd.bookmarks').text.strip().replace(',', ''))
        except AttributeError:
            self.__bookmarks = 0
        try:
            self.__hits = int(soup.select_one(':not(#workskin) .stats dd.hits').text.strip().replace(',', ''))
        except AttributeError:
            self.__hits = 0

        # TODO: self.__comments = []
        self.__chapters = [
            Chapter.parse_index(chapter) for chapter in soup.select(":not(#workskin) li.chapter #selected_id option")
        ]
        # HACK: no chapter selector exists if only 1 chapter exists so we need a different way to get chap link and name
        if len(self.__chapters) > 0:
            self.__last_chapter_url = self.__chapters[-1].url
        else:
            self.__last_chapter_url = url

    def __load_end_notes(self):
        print(self.__last_chapter_url)
        r = requests.get(self.__last_chapter_url)
        if r.status_code != 200:
            raise AO3Exception("Chapter not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        url_parts = self.__last_chapter_url.split('/')
        chapter_id = url_parts[-2] if len(url_parts[-1].strip()) == 0 else url_parts[-2]
        super()._check_property(self.__chapters)
        self.__chapters[-1] = Chapter(chapter_id, soup.select_one("#workskin .chapter"))


    @staticmethod
    def parse_listing(soup):
        work = Work()
        work.__url = f"{baseURL}{soup.select_one(':not(.userstuff).header h4.heading a:not([ref=author])').get('href')}"
        work.__work_id = Work.get_work_id_from_url(work.__url)
        last_chapter_elm = soup.select_one(':not(.userstuff).stats dd.chapters a')
        work.__last_chapter_url = work.__url if last_chapter_elm is None else f"{baseURL}{last_chapter_elm.get('href')}"
        #print("last chapter url: "+)
        work.__title = soup.select_one(':not(.userstuff).header h4.heading a:not([ref=author])').text.strip()
        work.__rating = soup.select_one(':not(.userstuff).required-tags li .rating span').text.strip()
        work.__category = soup.select_one(':not(.userstuff).required-tags li .category span').text.strip()
        work.__authors = \
            [User.parse_listing(elm) for elm in soup.select(':not(.userstuff).header .heading a[rel=author]')]
        work.__archive_warnings = \
            soup.select_one(':not(.userstuff).required-tags li .warnings span').text.strip().split(', ')
        work.__fandoms = [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) .fandoms a.tag')]
        work.__relationships = \
            [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) ul.tags li.relationships a')]
        work.__characters = [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) ul.tags li.characters a')]
        work.__tags = [Tag.parse_tag(elm) for elm in soup.select(':not(.userstuff) ul.tags li.freeforms a')]
        try:
            work.__summary = AO3Item._format_text(soup.select_one('.userstuff.summary'))
        except AttributeError:
            pass
        work.__language = soup.select_one(':not(.userstuff).stats dd.language').text.strip()
        work.__words = int(soup.select_one(':not(.userstuff).stats dd.words').text.strip().replace(',', ''))
        chapters = soup.select_one(":not(.userstuff).stats dd.chapters").text.strip().split('/')
        work.__chapter_count = int(chapters[0].replace(',', ''))
        work.__chapter_max = None if chapters[1] == '?' else int(chapters[1].replace(',', ''))
        try:
            work.__comment_count = \
                int(soup.select_one(':not(.userstuff).stats dd.comments').text.strip().replace(',', ''))
        except AttributeError:
            work.__comment_count = 0
        try:
            work.__kudos = int(soup.select_one(':not(.userstuff).stats dd.kudos').text.strip().replace(',', ''))
        except AttributeError:
            work.__kudos = 0
        try:
            work.__bookmarks = int(soup.select_one(':not(.userstuff).stats dd.bookmarks').text.strip().replace(',', ''))
        except AttributeError:
            work.__bookmarks = 0
        try:
            work.__hits = int(soup.select_one(':not(.userstuff).stats dd.hits').text.strip().replace(',', ''))
        except AttributeError:
            work.__hits = 0
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
        r = requests.get(url)
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
        super()._check_property(self.__work_id)
        return self.__work_id

    @property
    def title(self):
        super()._check_property(self.__title)
        return self.__title

    @property
    def url(self):
        super()._check_property(self.__url)
        return self.__url

    @property
    def authors(self):
        super()._check_property(self.__authors)
        return self.__authors

    @property
    def rating(self):
        super()._check_property(self.__rating)
        return self.__rating

    @property
    def archive_warnings(self):
        super()._check_property(self.__archive_warnings)
        return self.__archive_warnings

    @property
    def fandoms(self):
        super()._check_property(self.__fandoms)
        return self.__fandoms

    @property
    def relationships(self):
        super()._check_property(self.__relationships)
        return self.__relationships

    @property
    def characters(self):
        super()._check_property(self.__characters)
        return self.__characters

    @property
    def tags(self):
        super()._check_property(self.__tags)
        return self.__tags

    @property
    def summary(self):
        super()._check_property(self.__summary)
        return self.__summary

    @property
    def start_notes(self):
        super()._check_property(self.__start_notes)
        return self.__start_notes

    @property
    def end_notes(self):
        super()._check_property(self.__end_notes, self.__load_end_notes)
        return self.__end_notes

    @property
    def language(self):
        super()._check_property(self.__language)
        return self.__language

    @property
    def published(self):
        super()._check_property(self.__published)
        return self.__published

    @property
    def updated(self):
        super()._check_property(self.__updated)
        return self.__updated

    @property
    def words(self):
        super()._check_property(self.__words)
        return self.__words

    @property
    def chapter_count(self):
        super()._check_property(self.__chapter_count)
        return self.__chapter_count

    @property
    def chapter_max(self):
        super()._check_property(self.__chapter_max)
        return self.__chapter_max

    @property
    def comment_count(self):
        super()._check_property(self.__comment_count)
        return self.__comment_count

    @property
    def kudos(self):
        super()._check_property(self.__kudos)
        return self.__kudos

    @property
    def bookmarks(self):
        super()._check_property(self.__bookmarks)
        return self.__bookmarks

    @property
    def hits(self):
        super()._check_property(self.__hits)
        return self.__hits

    @property
    def chapters(self):
        super()._check_property(self.__chapters)
        return self.__chapters


class Chapter(AO3Item):
    __name = Unloaded()
    __id = Unloaded()
    __url = Unloaded()
    __number = Unloaded()
    __summary = Unloaded()
    __start_notes = Unloaded()
    __end_notes = Unloaded()
    __content = Unloaded()  # the text of a chapter converted to markdown
    __content_html = Unloaded()  # the original chapter html
    __work = Unloaded()

    def __init__(self, chapter_id=None, soup=None):
        if chapter_id is None:
            return
        self.__url = f'{baseURL}/chapters/{chapter_id}'
        self.__id = chapter_id
        self.load(soup)

    def load(self, soup=None):
        if soup is None:
            r = requests.get(self.__url)
            if r.status_code != 200:
                raise AO3Exception("Chapter not found.")
            soup = BeautifulSoup(r.text, 'lxml')
        name_parts = soup.select_one("#workskin .chapter .title").text.strip().split(' ')
        self.__name = ' '.join(name_parts[:2]) if len(name_parts) == 2 else ' '.join(name_parts[2:])
        self.__number = name_parts[1].replace(':', '')
        self.__summary = self._format_text(soup.select_one("#workskin .preface .summary .userstuff"))
        self.__start_notes = self._format_text(soup.select_one("#workskin .preface .notes:not(.end) .userstuff"))
        self.__end_notes = self._format_text(soup.select_one("#workskin .preface .end.notes .userstuff"))
        self.__content = None  # the text of a chapter converted to markdown
        self.__content_html = None  # the original chapter html
        self.__work = None

    @staticmethod
    def parse_index(soup):
        chapter = Chapter()
        parts = soup.text.strip().split(' ')
        chapter.__name = ' '.join(parts[1:])
        chapter.__url = f'{baseURL}/chapters/{soup.get("value")}'
        chapter.__number = parts[0][:-1]
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
        super()._check_property(self.__name)
        return self.__name

    @property
    def id(self):
        super()._check_property(self.__id)
        return self.__id

    @property
    def url(self):
        super()._check_property(self.__url)
        return self.__url

    @property
    def number(self):
        super()._check_property(self.__number)
        return self.__number

    @property
    def summary(self):
        super()._check_property(self.__summary)
        return self.__summary

    @property
    def start_notes(self):
        super()._check_property(self.__start_notes)
        return self.__start_notes

    @property
    def end_notes(self):
        super()._check_property(self.__end_notes)
        return self.__end_notes

    @property
    def content(self):
        super()._check_property(self.__content)
        return self.__content

    @property
    def content_html(self):
        super()._check_property(self.__content_html)
        return self.__content_html

    @property
    def work(self):
        super()._check_property(self.__work)
        return self.__work


class Tag(AO3Item):
    __name = Unloaded()
    __url = Unloaded()
    __type = Unloaded()
    __canonized = Unloaded()
    __parents = Unloaded()
    __synonyms = Unloaded()
    __mergers = Unloaded()
    __meta = Unloaded()
    __characters = Unloaded()
    __relationships = Unloaded()
    __tags = Unloaded()
    __works = Unloaded()

    def load(self):
        r = requests.get(f"{baseURL}/tags/{self.name.replace('/', '*s*')}/")
        if r.status_code != 200:
            raise AO3Exception("Tag not found.")
        soup = BeautifulSoup(r.text, 'lxml')
        self.__url = f"{baseURL}/tags/{self.name.replace('/', '*s*').replace(' ', '%20')}/"
        self.__name = soup.select_one('.header h2.heading').text.strip()
        desc = soup.select_one('.tag.home.profile p').text.strip()
        self.__type = desc.split(' ')[5]
        self.__canonized = "It's a common tag" in desc
        self.__parents = [self.parse_tag(elm) for elm in soup.select('.parent.listbox ul li a.tag')]
        self.__synonyms = [self.parse_tag(elm) for elm in soup.select('.synonym.listbox ul li a.tag')]
        self.__mergers = [self.parse_tag(elm) for elm in soup.select('.merger.module ul li a.tag')]
        self.__meta = [self.parse_tag(elm) for elm in soup.select('.meta.listbox a.tag')]
        self.__characters = [self.parse_tag(elm) for elm in soup.select('.characters.listbox ul li a.tag')]
        self.__relationships = [self.parse_tag(elm) for elm in soup.select('.relationships.listbox ul li a.tag')]
        self.__tags = [self.parse_tag(elm) for elm in soup.select('.freeforms.listbox ul li a.tag')]

    def __init__(self, name=None):
        if name is None:
            return
        self.__name = name
        self.load()

    @property
    def name(self):
        super()._check_property(self.__name)
        return self.__name

    @property
    def url(self):
        super()._check_property(self.__url)
        return self.__url

    @property
    def type(self):
        super()._check_property(self.__type)
        return self.__type

    @property
    def canonized(self):
        super()._check_property(self.__canonized)
        return self.__canonized

    @property
    def parents(self):
        super()._check_property(self.__parents)
        return self.__parents

    @property
    def synonyms(self):
        super()._check_property(self.__synonyms)
        return self.__synonyms

    @property
    def meta(self):
        super()._check_property(self.__meta)
        return self.__meta

    @property
    def characters(self):
        super()._check_property(self.__characters)
        return self.__characters

    @property
    def relationships(self):
        super()._check_property(self.__relationships)
        return self.__relationships

    @property
    def tags(self):
        super()._check_property(self.__tags)
        return self.__tags

    @property
    def works(self):
        if self.__works is None:
            r = requests.get(f'{self.__url}/works')
            if r.status_code != 200:
                raise AO3Exception("Unable to find works for this tag.")
            self.soup = BeautifulSoup(r.text, 'lxml')
            soup = self.soup
            work_count = \
                int(soup.select_one(":not(userstuff) h2.heading").text.strip().split(' ')[4].replace(",", "")) \
                    if soup.select_one(":not(userstuff).pagination") \
                    else int(soup.select_one(":not(userstuff) h2.heading").text.strip().split(' ')[0])
            self.__works = WorkPagination(f"{self.__url}/works", 20, work_count)
        return self.__works

    @staticmethod
    def parse_tag(soup):
        tag = Tag()
        tag.__name = soup.text.strip()
        tag.__url = f"{baseURL}/tags/{tag.__name.replace('/', '*s*').replace(' ', '%20')}/"
        if tag.__url[-6:] == "/works":  # links inconsistently append /works
            tag.__url = tag.__url[:-6]

        return tag
