LINES = {
    # Missing closing ]:
    "[The following forms may be based on or influenced by pCM *mooy `blind, weak-eyed'":
        "[The following forms may be based on or influenced by pCM *mooy `blind, weak-eyed']",
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
    # cf not in column 1:
    " cf. QEQc&l   eht                                                     bravo //                        [TK71]":
        "cf. QEQc&l   eht                                                     bravo //                        [TK71]",
    " cf. KCH      sojoot                                                  palo jiote                               [tk]":
        "cf. KCH      sojoot                                                  palo jiote                               [tk]",
    "BOGUS? KCH     q'ich                          vt        desgranar mazorca //         [gm]":
        "     ?KCH     q'ich                          vt        desgranar mazorca //         [gm]",
    # Concatenate two lines by replacing the first line with the concatenation and removing the second one:
    "EM+GQ *//tu7l-ul// ?`marmalade fruit' (Pouteria mammosa)":
        "EM+GQ *//tu7l-ul// ?`marmalade fruit' (Pouteria mammosa)  `sapodilla plum' (Manilkara achras)",
    "`sapodilla plum' (Manilkara achras)": "",
    #
    #LL+WM *ha7as         s         zapote //
    #`marmalade fruit' (Pouteria mammosa)
    #
    "LL+WM *ha7as         s         zapote //":
        "LL+WM *ha7as         s         zapote // `marmalade fruit' (Pouteria mammosa)",
    "`marmalade fruit' (Pouteria mammosa)": "",
    #pM *nhii7     s         suegro // father-in-law
    #                        yerno // man's son-in-law
    #                        `parent-in-law'; `son-in-law'
    "pM *nhii7     s         suegro // father-in-law":
        "pM *nhii7     s         suegro // father-in-law; yerno // man's son-in-law; `parent-in-law'; `son-in-law'",
    "                        yerno // man's son-in-law": "",
    "                        `parent-in-law'; `son-in-law'": "",
    #pM *7al7iib'        s         nuera // daughter-in-law
    #`woman's parent-in-law; daughter-in-law'
    "pM *7al7iib'        s         nuera // daughter-in-law":
        "pM *7al7iib'        s         nuera // daughter-in-law; `woman's parent-in-law; daughter-in-law'",
    "`woman's parent-in-law; daughter-in-law'": "",
}


def iter_lines(lines):
    # All lines that start with a 50 space offset are continuation lines.
    last = None
    for line in lines:
        if line.startswith(50 * " "):
            last += ' ' + line.strip()
        else:
            if last:
                yield from last.split('\n')
            last = LINES.get(line, line)
    if last:
        yield from last.split('\n')
