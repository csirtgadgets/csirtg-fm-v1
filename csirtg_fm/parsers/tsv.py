from csirtg_fm.parsers.delim import Delim


class Tsv(Delim):

    def __init__(self, **kwargs):
        self.delim = "\t"

        super(Tsv, self).__init__(**kwargs)


Plugin = Tsv
