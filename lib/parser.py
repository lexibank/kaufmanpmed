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
import pathlib
import functools
import dataclasses

from .languoids import match_languoids
from .lines import iter_lines, fix_blocks

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
@dataclasses.dataclass
class Gloss:
    spanish: str = None
    english: str = None

    @classmethod
    def from_string(cls, s):
        sp, _, en = s.partition('//')
        return cls(sp.strip() or None, en.strip() or None)

    def __str__(self):
        return '{} // {}'.format(self.spanish or '', self.english or '')


@dataclasses.dataclass
class Reflex:
    lang: str
    form: str = None
    gloss: Gloss = None
    source: str = None
    comment: str = None
    pos: str = None
    orig_lang: str = None

    def __str__(self):
        return '    {}{}\t{}\t{}\t{}'.format(
            self.lang,
            '[{}]'.format(self.orig_lang) if self.orig_lang else '',
            self.form or '',
            self.pos or '',
            self.gloss,
        )

    @classmethod
    def from_line(cls, line):
        #
        # FIXME: Normalize line!
        # vt:idiomatic {.b'e7} pulsearlo [ERH],,SEE,,
        # vt:indir/instr (a)puntar [rifle] [ERH],,MEASURE,,
        # aj (adv?) temprano [ETR],,EARLY,,
        line = line.replace("(+ dir)[d]estirar", "(+ dir)[d]estirar")
        line = line.replace("vt (instr)ma", "vt (instr)  ma")

        linen = re.sub(
            r'(?P<pos>T|vt|vi|aj)\s*\(?\+\s*(?P<qual>[a-z]+)\)?\s//',
            lambda m: '{} + {}  //'.format(m.group('pos'), m.group('qual')),
            line)
        linen = re.sub(
            r'(?P<pos>T|vt|vi|aj)\s*\(?\+\s*(?P<qual>[a-z]+)\)?\s(?P<gloss>[a-z])',
            lambda m: '{} + {}  {}'.format(m.group('pos'), m.group('qual'), m.group('gloss')),
            linen)
        linen = re.sub(
            r'(?P<pos>T|vt|vi|aj):(?P<qual>[a-z/]+)\s(?P<add>\{.b\'e7}\s)?(?P<gloss>[a-z(])',
            lambda m: '{}:{} {}  {}'.format(m.group('pos'), m.group('qual'), m.group('add') or '', m.group('gloss')),
            linen)
        if linen != line:
            #print(line)
            line = linen

        #
        # Parse the language specification:
        lang, line = line.split(None, maxsplit=1) if re.search(r'\s', line) else (line, '')
        lang, orig_lang = match_languoids(lang)
        assert len(lang) == 1, 'reflexes must be assigned to a single variety'
        lang = lang[0]

        # Parse the source:
        source = re.search('\s*\[(?P<source>[a-zA-Z0-9\-& ():*,#.?]+)]$', line)
        if source:
            line = line[:source.start()].strip()
            source = source.group('source')

        if re.match(r'#[a-z\-]+\s+/', line):
            # Normalize whitespace between protoform and remainder.
            line = '{} {}'.format(*line.split(None, maxsplit=1))

        form, pos, gloss, comment = None, None, None, None
        comps = re.split(r'\s\s+', re.sub(r'//\s\s+', '// ', line))
        if len(comps) == 3:  # 3 multi-space separated "columns".
            form, pos, gloss = comps  # We assume these are form, PoS and gloss ...
            if pos.startswith('/') and pos.endswith('/'):  # ... unless PoS is part of the form ...
                form += ' {}'.format(pos)
                pos = None
            elif pos.startswith('[') and pos.endswith(']'):  # ... or a comment.
                comment = pos[1:-1].strip()
                pos = None
        elif len(comps) == 2:
            form, gloss = comps
        elif len(comps) == 1:
            form = comps[0]
        else:
            raise ValueError(line)

        if gloss and ':' in gloss:
            print(gloss)

        return cls(
            lang,
            form=form,
            gloss=Gloss.from_string(gloss) if gloss else None,
            source=source,
            pos=pos,
            comment=comment,
            orig_lang=orig_lang,
        )


class Dictionary:
    def __init__(self, p):
        p = pathlib.Path(p)
        self.full_lines = list(iter_lines(fix_blocks(p.read_text(encoding='utf8')).split('\n')))
        self.lines = [l[0] for l in self.full_lines]
        self.semantic_fields = []
        last_sf = None
        for sf, subfield, chunk in self._iter_semantic_fields(self.full_lines):
            self.semantic_fields.append(SemanticField(
                last_sf if subfield else sf,
                sf if subfield else None,
                chunk,
            ))
            if not subfield:
                last_sf = sf

    def __getitem__(self, item):
        if isinstance(item, int):
            return [etymon for etymon in self._iter_etyma() if etymon.page == item]
        for sf in self.semantic_fields:
            if sf.main == item or (sf.sub and sf.sub == item):
                return sf
        for etymon in self._iter_etyma():
            if etymon.protoform and item in etymon.protoform:
                return etymon
        raise KeyError(item)

    def _iter_etyma(self):
        for sf in self.semantic_fields:
            yield from sf.etyma

    @staticmethod
    def _iter_semantic_fields(lines):
        sf_title_pattern = re.compile(r'(?P<subfield>\s+)?%%?\s+(?P<title>[^%]+)%%?')
        sf_frame_pattern = re.compile(r'\s*%%%%[%]+')

        sf, subfield, chunk = None, False, []
        for line, page, lineno in lines:
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
            chunk.append((line, page, lineno))
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


@dataclasses.dataclass
class SemanticField:
    main: str
    sub: str
    lines: list

    @functools.cached_property
    def etyma(self):
        def iter_reflexes(lines):
            witness = None
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('['):  # Comments are assigned to the preceding reflex.
                    assert witness, line
                    witness.comment = line[1:-1].strip()
                else:
                    if witness:
                        yield witness
                    witness = Reflex.from_line(line)
            if witness:
                yield witness

        res = []
        for concept, protoform, witnesses, comments, page, line in iter_etyma(
                self.lines, self.main, self.sub):
            witnesses = list(iter_reflexes(witnesses))
            res.append(Etymon.from_data(concept, protoform, witnesses, comments, page, line))
        return res


@dataclasses.dataclass
class Protoform:
    lang: str
    form: str
    gloss: str
    pos: str = None
    comment: str = None
    number: str = None
    orig_lang: str = None

    def __str__(self):
        return '{}{}\t{}'.format(
            self.lang,
            '[{}]'.format(self.orig_lang) if self.orig_lang else '',
            self.form,
        )

    @classmethod
    def from_line(cls, protoform):
        def repl_apos(s):
            for k, v in [("man's", "man__s"), ("mother's", "mother__s")]:
                s = s.replace(k, v)
            return s

        def repl_underscore(s):
            for k, v in [("man's", "man__s"), ("mother's", "mother__s")]:
                s = s.replace(v, k)
            return s

        # Parse langspec:
        orig = None
        if protoform.startswith('*') or protoform.startswith('#'):
            langspec = None
        elif re.search(r'\s', protoform):
            langspec, protoform = protoform.split(None, maxsplit=1)
        else:
            langspec, protoform = protoform, None
        if langspec:
            res, orig = match_languoids(langspec)
            assert res
            langspec = '+'.join(res)

        comment, gloss, source, number, pos = [], [], None, None, None

        # Parse gloss:
        if protoform:
            protoform = repl_apos(protoform)
            # "STUFF" = `stuff';
            match = re.search(r'"(?P<g1>[^"]+)"(\s*(=\s*)?`(?P<g2>[^\']+)\')?;?', protoform)
            if match:
                gloss.append(match.group('g1'))
                if match.group('g2'):
                    gloss.append(match.group('g2'))
                protoform = protoform[:match.start()] + protoform[match.end():]
                if not match.group('g2'):
                    match = re.search(r' = (?P<g2>[a-z]+( [a-z]+)*)', protoform)
                    if match:
                        gloss.append(match.group('g2'))
                        protoform = protoform[:match.start()] + protoform[match.end():]
                protoform = protoform.lstrip(' ')

            match = re.search(r'`(?P<g>[^\']+)\'(\s+\((?P<spec>[^)]+)\))?', protoform)
            if match:
                assert not gloss, protoform
                gloss.append(match.group('g'))
                if match.group('spec'):
                    gloss.append(match.group('spec'))
                protoform = protoform[:match.start()] + protoform[match.end():]

            if gloss:
                gloss = [repl_underscore(gl) for gl in gloss]
            protoform = repl_underscore(protoform)

            while '[' in protoform:
                protoform, _, inbraces = protoform.partition('[')
                inbraces, _, rem = inbraces.partition(']')
                protoform += rem
                if inbraces in {'1', '2'}:
                    number = inbraces
                    protoform = protoform.rstrip(' ')
                elif 'TK' in inbraces:
                    assert not source
                    source = inbraces
                else:
                    comment.append(inbraces)

            pf, ingloss = '', False
            for s in re.split(r'(\s\s+)', protoform):
                if '//' in s:
                    ingloss = True
                if ingloss:
                    if s.strip():
                        gloss.append(s.strip())
                else:
                    pf += s
            protoform = pf.strip()

            for i, ss in enumerate(re.split(r'\s\s+', protoform)):
                if i == 0:
                    protoform = ss
                elif ss in {
                    "vt", "vi", "vt > passive", "vi < P",
                    "s", "P", "sv", "dir", "num",
                    "aj", "aj < P", "a(P)",
                    "reflexive pronoun"}:
                    pos = ss
                else:
                    gloss.append(ss)

        clean_gloss = []
        for gl in gloss:
            gl = gl.strip()
            if gl:
                if '//' in gl:
                    es, _, en = gl.partition('//')
                    if es.strip():
                        clean_gloss.append('{} [es]'.format(es.strip()))
                    if en.strip():
                        clean_gloss.append('{} [en]'.format(en.strip()))
                else:
                    clean_gloss.append(gl)

        gloss = '; '.join(clean_gloss)
        return cls(langspec, protoform, gloss, pos, '; '.join(comment), number, orig_lang=orig)


@dataclasses.dataclass
class Etymon:
    concept: Concept
    protoform: str
    reflexes: list[Reflex]
    comments: list
    page: int
    line: int

    @classmethod
    def from_data(cls, concept, protoform, witnesses, comments, page, line):
        if protoform:
            protoform = Protoform.from_line(protoform)
            if protoform.gloss and not concept:
                concept = Concept(protoform.gloss)

        return cls(concept, protoform, witnesses, comments, page, line)

    def __str__(self):
        res = []
        if self.concept:
            res.append('%% {} %%'.format(self.concept.name))
        res = [str(self.protoform) or '-']
        for w in self.reflexes:
            res.append('    {}'.format(w))
        return '\n'.join(res + [''])


def iter_etyma(lines, main, sub, rootid=0):
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
    protoform, witnesses, concept, comments = None, [], None, []
    start_page, start_lineno = None, None

    for line, page, lineno in lines:
        if start_page is None:
            start_page = page
        if start_lineno is None:
            start_lineno = lineno

        if line.startswith('          '):
            m = concept_pattern.fullmatch(line.strip())
            if m:
                concept = Concept(**m.groupdict())
                continue

        if re.fullmatch(r'xxxxxxx[x]+', line.strip()):
            if witnesses:
                yield concept, protoform, witnesses, comments, start_page, start_lineno
            start_lineno, start_page = lineno, page
            protoform, witnesses, concept, comments = None, [], None, []
            continue

        if re.fullmatch(r'=====[=]+', line.strip()):
            if witnesses:
                yield concept, protoform, witnesses, comments, start_page, start_lineno
            start_lineno, start_page = lineno, page
            protoform, witnesses, comments = None, [], []
            rootid += 1
            continue

        if line.startswith('    '):  # a witness line
            if line.strip().startswith('['):  # a witness comment
                assert line.strip().endswith(']'), line
            else:
                langs, _ = match_languoids(line.strip().split()[0])
                assert langs and len(langs) == 1, line.strip()
            witnesses.append(line)
        else:  # A line with no leading whitespace, presumably a reconstruction.
            if not line.strip():
                continue

            if concept_and_reconstruction_pattern.match(line):
                m = concept_and_reconstruction_pattern.match(line)
                concept = Concept(name=m.group('name'), species=m.group('species'))
                line = line.partition(m.group('sep'))[2].strip()

            if match_languoids(line.split()[0]):  # an etymon with an identified proto-language.
                if witnesses:
                    yield concept, protoform, witnesses, comments, start_page, start_lineno
                    # Concept is not reset!
                start_lineno, start_page = lineno, page
                witnesses, comments = [], []
                protoform = line
            elif line.startswith('*') or line.startswith('#'):
                # just a reconstruction without identified proto-language
                if witnesses:
                    yield concept, protoform, witnesses, comments, start_page, start_lineno
                start_lineno, start_page = lineno, page
                witnesses, comments = [], []
                protoform = line
            elif line.startswith('['):
                assert line.endswith(']')
                comments.append(line[1:-1].strip())
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
                assert len(line) > 5 and m, '{}: {}'.format(lineno, line)
                concept = Concept(name=line)

    if witnesses:
        yield concept, protoform, witnesses, comments, start_page, start_lineno
