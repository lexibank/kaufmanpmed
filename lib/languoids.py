import pathlib

from csvw.dsv import reader


LANGUOIDS = {
    r['ID']: r
    for r in reader(pathlib.Path(__file__).parent.parent / 'etc' / 'languages.csv', dicts=True)}


def match_languoids(s):
    comps = [ss for ss in s.split('+') if ss]
    if all(comp.replace('pre-', '').replace('?', '') in LANGUOIDS for comp in comps):
        return comps
