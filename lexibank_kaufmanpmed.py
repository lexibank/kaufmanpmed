import collections
import pathlib
import subprocess
import dataclasses

import pylexibank
from pyetymdict.dataset import Dataset as BaseDataset
from clldutils.path import ensure_cmd
from clldutils.misc import slug
from csvw.dsv import UnicodeWriter

from lib.parser import Dictionary, Gloss

# Customize your basic data.
# if you need to store other data in columns than the lexibank defaults, then over-ride
# the table type (pylexibank.[Language|Lexeme|Concept|Cognate|]) and add the required columns e.g.
#
#import attr
#
#@attr.s
#class Concept(pylexibank.Concept):
#    MyAttribute1 = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "kaufmanpmed"

    # register custom data types here (or language_class, lexeme_class, cognate_class):
    #concept_class = Concept

    # define the way in which forms should be handled
    form_spec = pylexibank.FormSpec(
        brackets={},#{"(": ")"},  # characters that function as brackets
        separators=";/,",  # characters that split forms e.g. "a, b".
        missing_data=('?', '-'),  # characters that denote missing data.
        strip_inside_brackets=True   # do you want data removed in brackets or not?
    )

    def cmd_download(self, args):
        with self.raw_dir.temp_download(
                'http://www.famsi.org/reports/01051/pmed.pdf', 'pmed.pdf') as p:
            subprocess.check_call([
                ensure_cmd('pdftotext'),
                '-nopgbrk',
                '-layout',
                str(p),
                str(self.raw_dir / 'pmed.txt')])

    def cmd_makecldf(self, args):
        from lib.parser import Protoform, Reflex

        self.schema(args.writer.cldf, with_cf=False, with_borrowings=False)
        args.writer.cldf.add_columns('CognatesetTable', 'Semantic_Field', 'Semantic_Subfield')

        forms = collections.defaultdict(list)
        cids = {}

        def add_form(obj):
            cid = slug(str(obj.gloss or 'nogloss')) or 'nogloss'
            if cid not in cids:
                try:
                    args.writer.add_concept(ID=cid, Name=str(obj.gloss))
                except:
                    print(obj)
                    raise
            try:
                return args.writer.add_lexemes(
                Language_ID=slug(obj.lang, lowercase=False),
                Parameter_ID=cid,
                Description=str(obj.gloss or ''),
                Value=obj.form,
                #Comment=form.comment,
                #Source=[str(ref) for ref in lang.refs] if lang else [str(ref) for ref in form.gloss.refs],
                #Doubt=getattr(form, 'doubt', False),
                )[0]
            except:
                print(obj)
                raise

        ne = 0
        words = 0
        sources = collections.Counter()
        pos = collections.Counter()
        glosses = collections.Counter()
        dictionary = Dictionary(self.raw_dir / 'pmed.txt')
        pfs, refl = [], []
        csid = 0
        lids = {}

        for lang in self.languages:
            del lang['Comment']
            lang['Is_Proto'] = lang.pop('Type') == 'proto language'
            lang['ID'] = slug(lang['ID'], lowercase=False)
            args.writer.add_language(**lang)
            lids[slug(lang['ID'], lowercase=False)] = 1

        for i in [1, 2]:
            for sf in dictionary.semantic_fields:
                assert sf.etyma
                for e in sf.etyma:
                    if i == 1:
                        if e.protoform and e.protoform.form and e.protoform.lang:
                            pfs.append(e.protoform)
                            if slug(e.protoform.lang, lowercase=False) not in lids:
                                assert e.protoform.lang == 'pP+pQp'
                            else:
                                fk = (e.protoform.lang, e.protoform.form, str(e.protoform.gloss or ''))
                                if fk not in forms:
                                    forms[fk].append(add_form(e.protoform))
                                else:
                                    pass  # FIXME: aggregate Source, comment, etc.

                    if i == 2:
                        fid = None
                        if e.protoform and e.protoform.form and e.protoform.lang:
                            fk = (e.protoform.lang, e.protoform.form, str(e.protoform.gloss or ''))
                            if fk in forms:
                                fid = forms[fk][0]['ID']

                        csid += 1
                        args.writer.objects['CognatesetTable'].append(dict(
                            ID=str(csid),
                            Name=e.protoform,
                            Description=str(e.concept),
                            Comment="\n".join(e.comments),
                            Semantic_Field=sf.main,
                            Semantic_Subfield=sf.sub,
                            Form_ID=fid,
                        ))

                    ne += 1
                    #words += len(e.witnesses)
                    sources.update([w.source for w in e.reflexes if w.source])
                    pos.update([w.pos for w in e.reflexes if w.pos])
                    for witness in e.reflexes:
                        if not witness.form:
                            continue

                        assert slug(witness.lang, lowercase=False) in lids
                        fk = (witness.lang, witness.form, str(witness.gloss))

                        if i == 1:
                            #
                            # FIXME: if the same word from the same language is listed with
                            # different glosses, should we just merge the glosses?
                            # AWA  #meb'a7 aj/s hue*rfano, pobre //              [a]
                            # AWA  meb'a7       pobre                            [OKMA]
                            # AWA  meb'a7       hue*rfano                        [OKMA]
                            #
                            refl.append(witness)
                            if fk not in forms:
                                try:
                                    forms[fk].append(add_form(witness))
                                except:
                                    print(witness.form)
                                    raise
                            words += 1
                            if witness.gloss:
                                glosses.update([dataclasses.astuple(witness.gloss)])
                        elif i == 2:
                            args.writer.add_cognate(
                                lexeme=forms[fk][0], Cognateset_ID=str(csid), #Doubt=cset.doubt
                            )

        with UnicodeWriter('glosses.csv') as w:
            w.writerow([f.name for f in dataclasses.fields(Gloss)] + ['count'])
            for pf, n in sorted(glosses.items(), key=lambda t: (t[0][0] or 'zzz', t[0][1] or 'zzz')):
                w.writerow(list(pf) + [n])
        print(ne, words)
        print(len(forms))
        #with UnicodeWriter('reflexes.csv') as w:
        #    w.writerow([f.name for f in dataclasses.fields(Reflex)])
        #    for pf in refl:
        #        w.writerow(dataclasses.astuple(pf))
        #with UnicodeWriter('protoforms.csv') as w:
        #    w.writerow([f.name for f in dataclasses.fields(Protoform)])
        #    for pf in pfs:
        #        w.writerow(dataclasses.astuple(pf))
