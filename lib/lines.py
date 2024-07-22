import re
import itertools
import dataclasses

LINES = {
    # Comment that relates to semantic field as a whole - just ignore:
    '               [these and more are found in TK "MCS"]': '',
    # Missing closing ]:
    "[The following forms may be based on or influenced by pCM *mooy `blind, weak-eyed'":
        "[The following forms may be based on or influenced by pCM *mooy `blind, weak-eyed']",
    "     MCH      xul                                      vt             to stick something through a crack      [tk 67-68":
        "     MCH      xul                                      vt             to stick something through a crack      [tk 67-68]",
    # Misplaced comment-final ]
    '[could be "earth is his leg", but cf. MAR 7us+7u w@s                  "earthquake\'s twoness]"':
        '[could be "earth is his leg", but cf. MAR 7us+7u w@s                  "earthquake\'s twoness"]',
    # Comments:
    'LOAN':
        '[LOAN]',
    'NOT IN KOT':
        '[NOT IN KOT]',
    'WEAK SET':
        '[WEAK SET]',
    'IS THIS JUST ONE SET?':
        '[IS THIS JUST ONE SET?]',
    '(first identified by McQuown)':
        '[first identified by McQuown]',
    "NOTE: GQ has *nh in place of *n; perhaps WM generally goes back to *nh":
        "[NOTE: GQ has *nh in place of *n; perhaps WM generally goes back to *nh]",
    "NOTHING MORE FOUND":
        "[NOTHING MORE FOUND]",
    "SAME AS FOREGOING/FOLLOWING?":
        "[SAME AS FOREGOING/FOLLOWING?]",
    "(aj= means prepound adjective)":
        "[aj= means prepound adjective]",
    "(pM *ty'eken   `driver ant') [TK 1978 13.7]":
        "[(pM *ty'eken   `driver ant') [TK 1978 13.7]]",
    "wol-VC   aj < P":
        "[wol-VC   aj < P]",
    # Misplaced protoform marker:
    "EM* k'ul.b'a7":
        "EM *k'ul.b'a7",
    "MAYBE pM *xil ~ GLL *xel":
        "pM *xil ~ GLL *xel\n[MAYBE]",
    '"EXIT of SUN" = `east\' *r-el.e.b\'.aal q\'iinh':
        '"EXIT of SUN" = `east\'\n*r-el.e.b\'.aal q\'iinh',
    "BONE of HEAD = `skull'; *b'aaq-eel jool.oom":
        "BONE of HEAD = `skull'\n*b'aaq-eel jool.oom",
    # Missing protoform marker:
    "ABS-ERG-mutz'-INFL ERG-Haty":
        "*ABS-ERG-mutz'-INFL ERG-Haty",
    # Inconsistent formatting of witness lines:
    "     TZO      #cucum                                   s              /kukub'/      palizada //":
        "     TZO      #cucum /kukub'/                            s                  palizada //",
    "     pCh       *7ax < 7ahx                    s                       ramo*n   // breadnut              [K&N 33]":
        "     pCh       *7ax < 7ahx                    s                       ramo*n // breadnut              [K&N 33]",
    "     CHR      ko(j)                                s                  from Yuc?      diente //":
        "     CHR      ko(j)                                s                      diente //\n       [from Yuc?]",
    "       YUK     #kanan    /k'a:n 7an/                   s              ?\"precious herb\"    yerba o mata que llaman":
        "       YUK     #kanan    /k'a:n 7an/                   s              ?\"precious herb\" yerba o mata que llaman",
    "      YUK      #tuchhub    [from Ch'olan]              s              dedo //                                  [m]":
        "      YUK      #tuchhub [from Ch'olan]              s              dedo //                                  [m]",
    # Missing language abbreviation:
    # CHR:
    "            k'iHn.aj, k'iHn.al, k'iHn.k'in.al  aj                       luke-warm, tepid":
        "     CHR         k'iHn.aj, k'iHn.al, k'iHn.k'in.al  aj                       luke-warm, tepid",
    "            k'iHn.t, k'iHn.kun.t               vt                       to (re)heat":
        "     CHR         k'iHn.t, k'iHn.kun.t               vt                       to (re)heat",
    "                      k'ijn.k'ijn rum tierra caliente":
        "     CHR         k'ijn.k'ijn rum tierra caliente",
    "                k'ijn.a7r                                sv             enojo, co*lera, envidia":
        "     CHR         k'ijn.a7r                                sv             enojo, co*lera, envidia",
    "                k'ijn.es                                 vt             incomodar, enojar, irritar, calentar":
        "     CHR         k'ijn.es                                 vt             incomodar, enojar, irritar, calentar",
    # MAMi:
"              wex xon (lejos)                                         lo avento*, lo lanzo*, lo tiro*          [OKMA]":
    "      MAMi     wex xon (lejos)                                         lo avento*, lo lanzo*, lo tiro*          [OKMA]",

    # cf not in column 1:
    " cf. QEQc&l   eht                                                     bravo //                        [TK71]":
        "cf. QEQc&l   eht                                                     bravo //                        [TK71]",
    " cf. KCH      sojoot                                                  palo jiote                               [tk]":
        "cf. KCH      sojoot                                                  palo jiote                               [tk]",
    "BOGUS? KCH     q'ich                          vt        desgranar mazorca //         [gm]":
        "     ?KCH     q'ich                          vt        desgranar mazorca //         [gm]",
}


@dataclasses.dataclass
class ContinuationLines:
    lines: list[str]
    matched: list[int] = dataclasses.field(default_factory=list)

    @property
    def all_matched(self):
        return not self.lines

    def maybe_replace(self, line):
        if all(i in self.matched for i, _ in enumerate(self.lines)):
            self.lines = []
        for i, l in enumerate(self.lines):
            if l.strip() == line.strip():
                self.matched.append(i)
                if i == 0:  # Matches the first line, return concatenation of all lines.
                    assert self.matched == [0]
                    return l + ' ' + ' '.join(self.lines[1:]), True
                return None, True
        return line, False


CONTINUATION_LINES = [
    ContinuationLines([
        "EM+GQ *//tu7l-ul// ?`marmalade fruit' (Pouteria mammosa)",
        "`sapodilla plum' (Manilkara achras)",
    ]),
    ContinuationLines([
        "LL+WM *ha7as         s         zapote //",
        "`marmalade fruit' (Pouteria mammosa)",
    ]),
    ContinuationLines([
        "pM *nhii7     s         suegro // father-in-law",
        "                        yerno // man's son-in-law",
        "                        `parent-in-law'; `son-in-law'",
    ]),
    ContinuationLines([
        "pM *7al7iib'        s         nuera // daughter-in-law",
        "`woman's parent-in-law; daughter-in-law'",
    ]),
    ContinuationLines([
        "pM *muq       enterrarlo // to bury it                 vt",
        "                   esconderlo // to hide it",
    ]),
    ContinuationLines([
        "pM *maam              s            abuelo // grandfather",
        "                                     nieto de hombre // man's grandchild",
    ]),
    ContinuationLines([
        "pM *tya7nh          s            ceniza // ashes",
        "                                 cal // quick-lime",
    ]),
    ContinuationLines([
        "     EpM      <7a-ku>, <7a-ka>, <7a-ku-la>, <7a-ku-lu> /7ahk/, /7ahk-u:l/",
        "                                             s         turtle",
    ]),
    ContinuationLines([
        "pM *kaab'          s            miel // honey",
        "                             abeja, colmena // bee",
    ]),
    ContinuationLines([
        "     EpM        <NAME-7a, NAME-ba-7a, k'a-ba-7a> /k'aab'aa7/",
        "                                               s         name",
    ]),
    ContinuationLines([
        "pM *hu7nh        s         amate // Ficus;",
        "                        papel // bark paper;",
        "                        libro // book",
    ]),
    ContinuationLines([
        "pM *pixp        s         tomate // tomato [+ TK 1978 7a]",
        "                          verruga, mezquino // wart",
        "                          mezquino, rui*n, miserable, \"codo\" / stindgy",
    ]),
    ContinuationLines([
        "pM *k'ah         s            amargo // bitter",
        "                           hiel, bilis // gall",
    ]),
    ContinuationLines([
        "     EpM (Ch) <yu-ta> /y-u:t/, <yu-ta-la> /y-u:t-a:l/",
        "                                              s                       ?food",
    ]),
]


def iter_fixed_lines(lines):
    for line, page, lineno in etymologies_lines(lines):
        for cl in CONTINUATION_LINES:
            if not cl.all_matched:
                line, replaced = cl.maybe_replace(line)
                if replaced:
                    break

        if line is None:
            continue

        line = line.replace('ANALYZE', '')  # Remove internal comment.
        line = LINES.get(line, line)
        for ll in line.split('\n'):
            yield ll, page, lineno


def iter_continued_lines(lines):
    # All lines that start with a 50 space offset are continuation lines.
    lines = list(iter_fixed_lines(lines))
    new, cont = [], []
    for line, page, lineno in reversed(lines):
        if line.startswith(50 * " "):
            cont.append(line.strip())
            continue
        if cont and not line.strip():
            # Ignore blank lines preceding continuation lines.
            continue
        if cont:
            line = '{} {}'.format(line, ' '.join(reversed(cont)))
            cont = []
        new.append((line, page, lineno))
    yield from reversed(new)


def iter_lines(lines):
    comment, in_comment = [], False

    for line, page, lineno in iter_continued_lines(iter_lines_with_pagenumbers(lines)):
        if in_comment:  # comment continuation line
            assert comment and not line.startswith(' '), '{}: {}'.format(lineno, line)
            comment.append(line.strip())
            if line.strip().endswith(']'):
                in_comment = False
                yield ' '.join(comment), page, lineno
                comment = []
            continue

        if line.startswith('['):
            assert not comment
            comment.append(line.strip())
            if not line.strip().endswith(']'):
                in_comment = True
            else:
                yield ' '.join(comment), page, lineno
                comment = []
            continue

        yield line, page, lineno


def iter_lines_with_pagenumbers(lines):
    page_number_line = re.compile(
        r'(?P<page>[0-9]+)\s+Kaufman: preliminary Mayan Etymological Dictionary')
    page = None

    for lineno, line in enumerate(lines):
        m = page_number_line.match(line)
        if m:
            if page:
                assert int(m.group('page')) == page + 1, line
            page = int(m.group('page'))
        else:
            yield line, 1 if page is None else page + 1, lineno


def etymologies_lines(lines):
    """
    Prune intro lines.
    """
    for line, page, lineno in itertools.takewhile(
            lambda line: 'T H E     E N D' not in line[0],
            itertools.dropwhile(
                lambda line: 'MAYAN ETYMOLOGIES' not in line[0],
                lines)
    ):
        if 'MAYAN ETYMOLOGIES' not in line:
            yield line, page, lineno
