import pathlib

from csvw.dsv import reader


LANGUOIDS = {
    r['ID']: r
    for r in reader(pathlib.Path(__file__).parent.parent / 'etc' / 'languages.csv', dicts=True)}


def match_languoids(s):
    comps = [ss for ss in s.split('+') if ss]
    comps = [comp.replace('pre-', 'p').replace('?', '').replace('+', '').replace('*', '')
             for comp in comps]
    comps = [{
        'pPoqom': 'pPOQ',
        'POQ': 'pPOQ',
        'pWas': 'pWa',
        'Was': 'pWa',
        'WAS+LL': 'pWa+LL',
        "Ch'olan": 'pCh',
        "Ch": 'pCh',
        "pCh'olan": 'pCh',
        'ColKaq': 'KAQcol',
        'Tzo': 'TZO',
        'Tze': 'TZE',
        'QEQc&l': 'QEQe',  # Same extension, same forms
        'QEQl&c': 'QEQe',
        'QEQw/e': 'QEQ',  # Only appears in one cognate set, with QEQc&l having identical form.
        'M': 'pM',
        'pChl': 'pCh',  # One case also has reflexes in, e.g., AKA, though.
        'pYUK': 'pYu',
        'pWAS': 'pWa',  # One reflex for an etymon of pM.
        # Missing proto-marker:
        'P': 'pP',
        'eKP': 'pKp',
        'Kp': 'pKp',
        'Mp': 'pMp',
        'Yu': 'pYu',
        'UK': 'pUK',
        'GK': 'pGK',
        'GM': 'pGM',
        'GQ': 'pGQ',
        'GTz': 'pGTz',
        'Tzp': 'pTzp',
        'Tz': 'pTzp',  # One etymon Tz+ with reflexes in TZO, TZE, MAM
        'pTz': 'pGTz',  # One etymon pTz with reflexes in pCh and CHR
        'pI': 'pIx',  # One etymon with reflexes in AWA and IXL.
        'Ip': 'pIx',  # One etymon with reflexes in AWA and IXL.
        'I': 'pIx',  # A handful of etyma with reflexes in AWA and IXL.
        'pIXL': 'pIx',  # One etymon for "pre-IXL"
        'TCh': 'pChT',  # Several etyma with reflexes in CHJ, TOJ (and in one case TUZ)
        'PQ': 'pPQ',
        'pQ': 'pQp',
        'QK': 'pGK',  # One etymon 'QK+' with reflexes from K'iche'an and MAM
        'Qp': 'pQp',  # Several etyma with reflexes in QAN, AKA, POP (and in two cases CHJ and TUZ)
        'Q': 'pGQ',  # One etymon Kp+Q with reflexes also in MCH
        # Misc.
        'pQa': 'pGQ',  # Two etyma, with reflexes in GQ
        'pMAM': 'MAM',  # appears only for one reflex: pMAM     mooyh
        'CM': 'pCM',  # Reconstructions assigned to a major genetic grouping
        'EM': 'pEM',  # Reconstructions assigned to a major genetic grouping
        'WM': 'pWM',  # Reconstructions assigned to a major genetic grouping
        #'NEG': 'LL+pCM', ?
    }.get(comp, comp) for comp in comps]
    if all(comp in LANGUOIDS for comp in comps):
        comps = sorted(comps)
        return comps, s if '+'.join(comps) != s else None
