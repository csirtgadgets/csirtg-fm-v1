from csirtg_fm.parsers.delim import Delim


class Pipe(Delim):

    def __init__(self, **kwargs):
        self.delim = "\s{2,}|\s{2,}"

        super(Pipe, self).__init__(**kwargs)


Plugin = Pipe
