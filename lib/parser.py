"""
Note: Quite a few maps from FAMSI are in LL-MAP, with extracted geojson!
http://www.famsi.org/maps/index.html

From https://www.cs.utexas.edu/~tandy/law-paper.pdf
Danny Law, Mayan Historical Linguistics in a New Age, Language and Linguistics Compass 7/3 (2013): 141–156, 10.1111/lnc3.12012

>  The baseline for most modern work
on Mayan historical linguistics, however, was established by Terrence Kaufman, a student
> of McQuown’s, who carried out extensive elicitation and survey-based linguistic research
> on Mayan languages. The quality and quantity of the linguistic materials gathered by
> Kaufman were orders of magnitude beyond anything previously used to develop
> hypotheses about Mayan prehistory. The family tree that Kaufman proposed in 1964, and
> then revised slightly in publications a few years later (Kaufman 1969, 1972) has remained
> the default model of genetic relations among Mayan languages for nearly half a century.

"""
import re
import itertools
import dataclasses

from .languoids import match_languoids
from .lines import iter_lines

#
# FIXME: handle continuation lines
"""
     TUZ    b'eha7                                  s              arroyo; 'sale un poco de agua en algun
                                                                      ladero/cerro' [ETR] //                 [TK67-68]
"""
#
# FIXME: explanations:
"""
(aj= means prepound adjective)
"""
#

"""

Since the etymologies (or cognate sets) are listed by semantic field,
occasionally parts of a single etymology have (inadvertently) been cited in
more than one place. TK would be glad if any cases that have escaped his
eye were brought to his attention.


That format is:
lexical item; grammatical code; gloss; data source

The total number of resulting etymologies was about 3000.

These etymologies are ordered by semantic field. Etymologies of the same
gloss are adjacent to one another. Etymologies of related meaning are in
the neighborhood of each other.

Some forms are cited from colonial period sources. When the phonology can
be established except for vowel length, accent, and glottal stop, the forms
are respelled with PFLM symbols but preceded by #. Where this is not
possible, the forms are enclosed in angle brackets, thus <abc>. Forms cited
from Epigraphic Mayan are cited in angle brackets, with signs in the
script separated by hyphens, thus <ba-la-ma>.



entries that have a common root are separated by two blank lines

sets of entries that have a common root are separated from adjacent (sets
of) entries that have a different root by =====

sets of entries that have the same or semantically related gloss are
bounded by xxxxx

"""


def parse_witness():
    """
    langcode   form   pos?   gloss, spanish // english   source

      YUK    #mam                               s         padre de madre, primo //           [m]

    comments on pos: (-itz), (-atz), ...

     TUZ        7i:ch                                   s3 (-itz) marido [ETR] [ERH] //                [TK67-68]

    """


def iter_lines_with_pagenumbers_stripped(lines):
    page_number_line = re.compile(
        r'(?P<page>[0-9]+)\s+Kaufman: preliminary Mayan Etymological Dictionary')
    page = None

    for line in lines:
        m = page_number_line.match(line)
        if m:
            if page:
                assert int(m.group('page')) == page + 1, line
            page = int(m.group('page'))
        else:
            yield line
            #yield 51 if page is None else page + 1, line


def etymologies_lines(lines):
    for line in itertools.takewhile(
        lambda line: 'T H E     E N D' not in line,
        itertools.dropwhile(
            lambda line: 'MAYAN ETYMOLOGIES' not in line,
            iter_lines_with_pagenumbers_stripped(lines))
    ):
        if 'MAYAN ETYMOLOGIES' not in line:
            yield line


def iter_semantic_fields(lines):
    """
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
     %% COLOR %%
     %%%%%%%%%%%
                                   WHITE
    """
    sf_title_pattern = re.compile(r'(?P<subfield>\s+)?%%?\s+(?P<title>[^%]+)%%?')
    sf_frame_pattern = re.compile(r'\s*%%%%[%]+')

    sf, subfield, chunk = None, False, []
    for line in lines:
        m = sf_frame_pattern.fullmatch(line)
        if m:
            continue
        m = sf_title_pattern.fullmatch(line)
        if m:
            if sf and chunk:
                yield sf, subfield, chunk
                sf, subfield, chunk = None, False, []
            sf = m.group('title').strip()
            subfield = bool(m.group('subfield'))
            continue
        chunk.append(line)
    assert sf, chunk
    yield sf, subfield, chunk


@dataclasses.dataclass
class Concept:
    name: str
    species: str = None
    comment: str = None

    def __str__(self):
        res = self.name
        if self.species:
            res += ' ({})'.format(self.species)
        if self.comment:
            res += ' [{}]'.format(self.comment)
        return res


def parse_semantic_field(lines, main, sub, rootid=0):
    """
[A-Z0-9,./-;]

(Solanum spp.)
[introduced after XXXX BCE]
    """
    #if sub:
    #    print('    ' + sub)
    #else:
    #    print(main)
    concept_pattern = re.compile(
        r'(?P<name>[A-Z0-9,./\-; ]+)(\((?P<species>[A-Za-z. ]+)\))?(\[(?P<comment>[^]]+)])?')
    concept_and_reconstruction_pattern = re.compile(
        r'(?P<name>\"[^"]+\"(\s+=[^;,(]+)?)(\((?P<species>[A-Za-z. ]+)\))?(?P<sep>[;,]).*')

    #
    # FIXME: handle multiple comments per reconstruction, look for "following form"!
    #

    comments = []
    comment, in_comment = [], False
    concept = None
    protoform = None
    witnesses = []

    for line in iter_lines(lines):
        if in_comment:
            assert comment and not line.startswith(' '), line
            comment.append(line.strip())
            if line.strip().endswith(']'):
                in_comment = False
                comment[-1] = comment[-1][:-1]
                comments.append(' '.join(comment))
                comment = []
            continue

        if line.startswith('          '):
            m = concept_pattern.fullmatch(line.strip())
            if m:
                concept = Concept(**m.groupdict())
                continue

        if re.fullmatch(r'xxxxxxx[x]+', line.strip()):
            if witnesses:
                yield concept, protoform, witnesses, comments
            protoform, witnesses, concept, comments = None, [], None, []
            continue

        if re.fullmatch(r'=====[=]+', line.strip()):
            if witnesses:
                yield concept, protoform, witnesses, comments
            protoform, witnesses, concept, comments = None, [], None, []
            rootid += 1
            continue

        if line.startswith('    '):  # a witness line
            #if not protoform and not witnesses:
            #    #print(line)
            #    pass
            witnesses.append(line)
        else:  # a reconstruction
            if not line.strip():
                continue

            if concept_and_reconstruction_pattern.match(line):
                m = concept_and_reconstruction_pattern.match(line)
                concept = Concept(name=m.group('name'), species=m.group('species'))
                line = line.partition(m.group('sep'))[2].strip()

            if match_languoids(line.split()[0]):  # an etymon
                #
                # FIXME: yield a cognate set!
                #
                if witnesses:
                    if witnesses:
                        yield concept, protoform, witnesses, comments
                    protoform, witnesses, comments = None, [], []
                protoform = line
                #print(concept)
                pass
            elif line.startswith('*') or line.startswith('#'):
                if witnesses:
                    if witnesses:
                        yield concept, protoform, witnesses, comments
                    protoform, witnesses, comments = None, [], []
                protoform = line
            elif line.startswith('['):
                comment.append(line[1:].strip())
                if not line.strip().endswith(']'):
                    in_comment = True
                else:
                    comment[-1] = comment[-1][:-1]
            elif line.startswith('cf. '):  # a "see also" witness
                pass
            elif line == 'cf.':
                #
                # FIXME: introduces a group of "see also" witnesses!
                #
                pass
            elif line.startswith('?  '):  # dubious witness
                #
                # FIXME: handle!
                #
                pass
            else:
                # its to (in)
                m = re.fullmatch(r'"?([A-Z0-9]+|to)(\s+([A-Z\-0-9]+|its|of|to|\(in\)|\+))*"?(\s+(=\s+)?`?[a-z/, ]+\'?)?', line)
                assert len(line) > 5 and m, line
                concept = Concept(name=line)


def parse(lines):
    last_sf = None

    for sf, subfield, chunk in iter_semantic_fields(etymologies_lines(lines)):
        parse_semantic_field(
            chunk,
            last_sf if subfield else sf,
            sf if subfield else None,
        )
        if not subfield:
            last_sf = sf
