# This is a sample Python script.
import datetime
from dataclasses import dataclass
import re

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
ctrl_generator = (f"jb{str(n).rjust(10, "0")}" for n in range(100000000))

@dataclass
class PublishingInfo:
    publisher_name: str
    publishing_date: str  # NEEDS TO BE FOUR CHARS LONG
    publishing_loc: str = "USA"
    publishing_country_code : str= "xxu" # should be a country code. xxu is USA
    publishing_lang: str = "eng"


def build_leader(record_status=None, record_type=None, bib_level=None):
    if not record_status: record_status = 'n'
    if not record_type: record_type = 'a'
    if not bib_level: bib_level = 'm'
    leader = Field("000", f"00000{record_status}{record_type}{bib_level}##2200000###4500")
    assert len(leader.subfields) == 24
    return leader


def build_ctrl():
    return Field("003", next(ctrl_generator))


def build_datetime():
    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".0"
    assert len(time_str) == 16
    return Field("005", time_str)


def build_fixed_len_data_elms(pub: PublishingInfo,
                              pub_date_type: str = None):  # type is s (single year) probably, or "c" for current periodical
    pub_date_type = "s" if not pub_date_type else pub_date_type
    date_str = datetime.datetime.now().strftime("%y%m%d")
    assert len(date_str) == 6
    date2: str = "####"
    date1 = pub.publishing_date
    if pub_date_type == "c":  # for periodicals
        date2 = "9999"
    pub_country = pub.publishing_country_code
    pub_lang = pub.publishing_lang
    full_str = f"{date_str}{pub_date_type}{date1}{date2}{pub_country}{'#' * 17}{pub_lang}##"
    assert len(full_str) == 40
    return Field("008", date_str)


class Subfield:
    def __init__(self, tag, text, ending=None, prefix=None):
        self.tag = tag
        self.text = text
        self.ending = "" if not ending else ending
        self.prefix = "" if not prefix else prefix

    def __str__(self):
        return f"{self.prefix}${self.tag}{self.text}{self.ending}"


class Field:
    def __init__(self, tag, subfields: Subfield | list[Subfield] | str = None, indicator=None, suffix=None):
        self.tag = tag
        self.indicator = "" if not indicator else indicator
        self.subfields = subfields
        if type(subfields) in [str, Subfield]:
            self.subfields = [subfields]
        self.suffix = "" if not suffix else suffix

    def add_subfield(self, subfield: Subfield):
        self.subfields.append(subfield)

    def add_subfield_by_elms(self, tag, text, ending=None, prefix=None):
        self.add_subfield(Subfield(tag, text, ending, prefix))

    def change_indicator(self, new_ind):
        self.indicator = new_ind

    def __str__(self):
        return f"={self.tag} {self.indicator}{"".join([str(subfield) for subfield in self.subfields])}{self.suffix}"


class LibraryItem:
    def __init__(self, name, item_type):
        self.name = name
        assert item_type in ('o', 'a', 'r', 't')
        self.type = item_type


class Book(LibraryItem):
    def __init__(self, authors: list[str], publish_info: PublishingInfo, title: str, subtitle=None,
                 ISBN=None, LCCN=None, DDC=None, edition : int = None,
                 curr_loc=None, notes=None, item_type=None, is_periodical=False):
        if not item_type:
            item_type = "a"
        assert item_type in ('a', 't')
        super().__init__(title, item_type)
        self.authors = authors
        self.publish_info = publish_info
        self.subtitle = subtitle
        self.ISBN = re.sub(r'\W+', '', ISBN)
        self.LCCN = LCCN
        self.DDC = DDC
        self.edition = None
        self.location = curr_loc
        self.notes = "" if not notes else notes
        self.is_periodical = is_periodical


        self.libraryID = "THETACHI"
        self.MARCInfo = []


    def build_MARC00_info(self) -> None:
        """
        Builds leader, ctrl number, ID (!?), datetime, fixed elems,  possibly ISBN, and cataloguing agency
        :return:
        """
        self.MARCInfo.append(build_leader('n', self.type, 'm'))
        self.MARCInfo.append(build_ctrl())
        self.MARCInfo.append(Field("003", self.libraryID))
        self.MARCInfo.append(build_datetime())
        self.MARCInfo.append(build_fixed_len_data_elms(self.publish_info, "c" if self.is_periodical else None))
        if self.ISBN:
            self.MARCInfo.append(Field("020", [Subfield("a", self.ISBN)], "##"))
        self.MARCInfo.append(
            Field("040", [
                Subfield("a", self.libraryID), Subfield("c", self.libraryID)
            ], "##")
        )

    def create_1xx(self):
        hundred_item: Field
        if "theta chi" in self.authors[0].lower():
            hundred_item = Field("110")
            hundred_item.add_subfield_by_elms("a", "Theta Chi")
            hundred_item.add_subfield_by_elms("b", "Beta Nu")
            hundred_item.add_subfield_by_elms("d", self.publish_info.publishing_date)
            hundred_item.change_indicator("2#")
            return hundred_item
        hundred_item = Field("100", suffix=".")
        if "," in self.authors[0]:
            hundred_item.change_indicator("1#")
        else:
            hundred_item.change_indicator("0#")
        if self.authors[0] == "Multiple":
            hundred_item.add_subfield_by_elms("a", "Various Authors")
        else:
            hundred_item.add_subfield_by_elms("a", self.authors[0])
        return hundred_item

    def build_1xx(self):
        self.MARCInfo.append(self.create_1xx())

    def build_2xx(self):
        title = Field("245")
        title.add_subfield_by_elms("a", self.name)
        stitle = Subfield("b", self.subtitle, prefix=" :")
        title.add_subfield(stitle)
        responsibility = Subfield("c", "")
        if self.authors[0] != "Multiple":
            if len(self.authors) > 3:
                responsibility.text = f"{self.authors[0]} et. al"
            else:
                responsibility.text = ";".join(self.authors)
        elif len(self.authors) > 1:
            responsibility.text = "Various Authors; " + ";".join(self.authors[1:])
        else:
            responsibility.text = "Various Authors"

        title.add_subfield(responsibility)

        funny_starts = ["A ", "An ", "The "]
        second_ind = "0"
        for funny_start in funny_starts:
            if self.name.startswith(funny_start):
                second_ind = str(len(funny_start))
                break

        title.change_indicator(f"1{second_ind}")

        self.MARCInfo.append(title)

        if self.edition:
            edition_field = Field("250", Subfield("a", f"{self.edition} ed."), "##")
            self.MARCInfo.append(edition_field)

        imprint = Field("260", suffix=".", indicator="##")
        imprint.add_subfield_by_elms("a", self.publish_info.publishing_loc)
        imprint.add_subfield_by_elms("b", self.publish_info.publisher_name, prefix=" :")
        imprint.add_subfield_by_elms("c", self.publish_info.publishing_date, prefix=",")

        self.MARCInfo.append(imprint)

    def build_3xx(self):
        physical_desc = Field("300", indicator="##")
        physical_desc.add_subfield_by_elms("a", "1 v.")
        physical_desc.add_subfield_by_elms("c", "cm.", prefix=" ;")
        self.MARCInfo.append(physical_desc)







class MARCRecord:
    def __init__(self, book: Book):
        self.book = book
        self.fields = []
