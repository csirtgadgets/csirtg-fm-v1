from csirtg_fm.parsers.delim import Delim


class Csv(Delim):

    def __init__(self, **kwargs):
        self.delim = ","

        self.strip = '"'

        super(Csv, self).__init__(**kwargs)


Plugin = Csv
