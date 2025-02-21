import re
import itertools
import dataclasses

BLOCKS = {
    """\
     EpM(Ch)   <RED-ch'o-ko> /chak=ch'ok/                             infant
     EpM(Ch)   <ch'o-ko> /ch'ok/                                      child, sprout; young, unripe
     EpM(Ch)   <ch'o-ko-le> /ch'oklel/                                youth
GTz *ch'ok ?< **ch'oq
""": """\
GTz *ch'ok ?< **ch'oq
     EpM(Ch)   <RED-ch'o-ko> /chak=ch'ok/                             infant
     EpM(Ch)   <ch'o-ko> /ch'ok/                                      child, sprout; young, unripe
     EpM(Ch)   <ch'o-ko-le> /ch'oklel/                                youth
    """,
    """\
========================================================================
                              OVER
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                              OVER
""",
    """\
=========================================================================

                                  CHARCOAL
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                                  CHARCOAL
""",
    """\
=========================================================================
                                   SOOT
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                                   SOOT
""",
    """\
                             PORCUPINE, STICKER BEAR
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                             PORCUPINE, STICKER BEAR
""",
    """\
=========================================================================

GREEN DEER
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                              GREEN DEER

""",
    """\
==========================================================================
                         GREEN DEERFLY
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                         GREEN DEERFLY
""",
    """\
========================================================================
                              STANDING
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                              STANDING
""",
    """\
=========================================================================
                                   160
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                                   160
""",
    """\
=========================================================================
                                   400
""": """\
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                                   400
"""
}

LINES = {
    "NEG *tyaam":  # negated form following after non-negated.
        "pM *NEG tyaam",
    # Prevent parsing of "light" as atomic gloss:
    "Was+WM *7ut     vt           to do it (`light' generic transitive verb); to say it":
        "Was+WM *7ut     vt           to do it (light generic transitive verb); to say it",
    # Re-order reconstruction and gloss:
    "pM \"HAND of QUERN\" = muller; *u-q'ab' kaa7":
        "pM *u-q'ab' kaa7  \"HAND of QUERN\" = muller",
    "EM+GQ \"SHIT of LOUSE\" = `nit'; pM *u-tzaa7 7uk'":
        "pM *u-tzaa7 7uk'  \"SHIT of LOUSE\" = `nit'",
    "GK \"THORN POSSUM\" = `sticker bear, porkypine'; Kp *ki7x-a huhty'":
        "GK+Kp *ki7x-a huhty'  \"THORN POSSUM\" = `sticker bear, porkypine'",
    "EM+GQ \"FLOWER of WINTER.SQUASH\", *u-xum.a7k(-iil) q'ohq'":
        "EM+GQ *u-xum.a7k(-iil) q'ohq'  \"FLOWER of WINTER.SQUASH\"",
    "CM \"ARM of TREE\" = branch; *u-q'ab' (tyee7)":
        "CM *u-q'ab' (tyee7)  \"ARM of TREE\" = branch",
    "GQ \"MAIZE of FOOT\" = toe; *r-ixi7m-aal FOOT":
        "GQ *r-ixi7m-aal FOOT  \"MAIZE of FOOT\" = toe",
    "EM \"FACE of KNEE\" = shin'; *u-Haty ty'ehk":
        "EM *u-Haty ty'ehk  \"FACE of KNEE\" = `shin'",
    "LL+WM \"BONE of FACE\" = skull; *u-b'aaq-eel ERG-Haty":
        "LL+WM *u-b'aaq-eel ERG-Haty  \"BONE of FACE\" = skull",
    "EM+ \"PIP of FACE\" = eye, *b'aq' Haty":
        "EM+ *b'aq' Haty  \"PIP of FACE\" = eye",
    "\"MAIZE of HAND\" = finger; GQ *r-ixi7m-aal ERG-q'ab'":
        "GQ *r-ixi7m-aal ERG-q'ab'  \"MAIZE of HAND\" = finger",
    '"EXIT of SUN" = `east\' *r-el.e.b\'.aal q\'iinh':
        '*r-el.e.b\'.aal q\'iinh  "EXIT of SUN" = `east\'',
    "BONE of HEAD = `skull'; *b'aaq-eel jool.oom":  # introduces a duplicate!
        "CM *b'aaq-eel jool.oom  \"BONE of HEAD\" = `skull'",
    # Turn alternative readings into comments:
    "pM (or pCh+) *7anaam [maybe (probably) a loan from Yokot'an to Wasteko]":
        "pM [or pCh+] *7anaam [maybe (probably) a loan from Yokot'an to Wasteko]",
    "EM+ *patz (cf. Nawa pach-tli)":
        "EM+ *patz [cf. Nawa pach-tli]",
    "MAM /naayaj/ from Soke *7anh=naji7":
        "MAM /naayaj/ [from Soke *7anh=naji7]",
    "GM+ *naq' (passive)":
        "GM+ *naq' [passive]",
    "Chis *k'anal [no *nh, maybe *q'] < **q'an.aal":
        "Chis *k'anal [no *nh, maybe *q'] [< **q'an.aal]",
    "GLL? #k'uk'um   `feather' < **q'u7q'":
        "GLL? #k'uk'um   `feather' [< **q'u7q']",
    "#kut(u) from Nawa /koto/":
        "#kut(u) [from Nawa /koto/]",
    "pM *t'iiw    `hawk' [+ TK 1978 14.] OR *t'ihw":
        "pM *t'iiw    `hawk' [+ TK 1978 14.] [OR *t'ihw]",
    "Hue *HEAD of MOUNTAIN `summit'; Hue *wi7 witz":
        "Hue *wi7 witz \"HEAD of MOUNTAIN\" = `summit'",
    "Hue *chum    ~ GK *chom":
        "Hue *chum    [~ GK *chom]",
    "GLL *tahb'     `20'     [TK 1978 7a])":
        "GLL *tahb'     `20'     [TK 1978 7a]",
    "Kp to FEEL it [as] GOOD *7utz na7":
        "Kp *7utz na7 \"to FEEL it [as] GOOD\"",
    "EM+ Hue #mo7otz [diffused]":
        "EM+Hue #mo7otz [diffused]",
    "Mp GO.OUT.AWAY SUN":
        "Mp \"GO.OUT.AWAY SUN\"",
    "Hue (GQ+GM) *7ix=7ajaaw":
        "Hue *7ix=7ajaaw",
    "pM (EM+Q) *ko7k' `tiny' [+ TK 1978 11b.c]":
        "pM *ko7k' `tiny' [+ TK 1978 11b.c]",
    "eGK (CM?) *yenh":
        "pGK *yenh",
    "pCM *tuus      s     flor de muerto // marigold [Tagetes electa]":
        "pCM *tuus      s     flor de muerto // marigold (Tagetes electa)",
    "Kp //*7i7h.a.oom// > *7i7hoom":
        "Kp /*7i7h.a.oom/ > *7i7hoom",
    "pGK *IT WORKS = `it is useful'":
        "pGK \"IT WORKS\" = `it is useful'",
    "CM *kaan `snake' = `cramp'":
        "CM *kaan \"snake\" = `cramp'",
    "CM *GREEN STONE = `river rock'":
        "CM \"GREEN STONE\" = `river rock'",
    "CM #mis [varied forms] (origin unclear; maybe from Nawa mis-tli)":
        "CM #mis [varied forms] [origin unclear; maybe from Nawa mis-tli]",
    "pM *t'in   `to hit' [TK 1978 14.19a] (cf. pM *t'in `taut')":
        "pM *t'in   `to hit' [TK 1978 14.19a] [cf. pM *t'in `taut']",
    "EM *t'in    `fatly stretched out' [TK 1978 14.19b] (see pM *t'in `taut']":
        "EM *t'in    `fatly stretched out' [TK 1978 14.19b] [see pM *t'in `taut']",
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
    "GLL *t'u7l (pM *t'ul) `rabbit' [TK 1978 14.15] (Classic Mayan innovation?)":
        "GLL *t'u7l (pM *t'ul) `rabbit' [TK 1978 14.15] [Classic Mayan innovation?]",
    "GLL *t'ox   `to split' [+ TK 1978 14.16] (Classic Mayan innovation?)":
        "GLL *t'ox   `to split' [+ TK 1978 14.16] [Classic Mayan innovation?]",
    "pM *t'ib'    `on all fours' [TK 1978 14.17] (Classic Mayan innovation?)":
        "pM *t'ib'    `on all fours' [TK 1978 14.17] [Classic Mayan innovation?]",
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
    "pYu wich'":
        "pYu *wich'",
    "EM* k'ul.b'a7":
        "EM *k'ul.b'a7",
    "MAYBE pM *xil ~ GLL *xel":
        "pM *xil ~ GLL *xel\n[MAYBE]",
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
    "      TUZ     tza7.a-:n                                   vi:antip       cagar   [ETR][ERH] //                   [TK67-68]":
        "      TUZ     tza7.a-:n                                   vi:antip       cagar [ETR][ERH] //                   [TK67-68]",
    "     YUK      koj                                      s              //j// (m)         leo*n // cougar   [mq]":
        "     YUK      koj                                      s              //j// (m); leo*n // cougar   [mq]",
    "    EpM (Ch) <yu-ta> /y-u:t/, <yu-ta-la> /y-u:t-a:l/":
        "    EpM(Ch) <yu-ta> /y-u:t/, <yu-ta-la> /y-u:t-a:l/",
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


def fix_blocks(text):
    for k, v in BLOCKS.items():
        assert k in text
        text = text.replace(k, v)
    return text


@dataclasses.dataclass
class ContinuationLines:
    lines: list[str]
    concatenated: str = None
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
                    assert self.matched == [0], l
                    if self.concatenated:
                        return self.concatenated, True
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
    ContinuationLines(
        [
            "      TZO       ta ERG-ich-on, 7ich-on-il               rn             in front of N, opposite N, on the front   [rml]",
            "                                                                          side of N",
        ],
        concatenated="      TZO       ta ERG-ich-on, 7ich-on-il               rn             in front of N, opposite N, on the front side of N  [rml]"
    ),
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

        line = line.replace('ANALYZE', '').replace('*//tu7l-ul//', '*/tu7l-ul/')  # Remove internal comment.
        line = LINES.get(line, line).replace('eGK', 'pGK')
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
