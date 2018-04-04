from csirtg_smrt.parsers.delim import Delim


class Csv(Delim):

    def __init__(self, **kwargs):
        self.pattern = ","

        super(Csv, self).__init__(**kwargs)


Plugin = Csv
