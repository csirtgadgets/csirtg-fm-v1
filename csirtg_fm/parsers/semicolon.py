from csirtg_fm.parsers.delim import Delim


class Semicolon(Delim):

    def __init__(self, **kwargs):
        self.delim = "[\s+]?;[\s+]?"

        super(Semicolon, self).__init__(**kwargs)


Plugin = Semicolon
