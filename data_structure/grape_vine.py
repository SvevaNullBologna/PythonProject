from pathlib import Path

class grape_vine():
    def __init__(self):
        self.basefolder = None


    def load_grape_vine(self,basefolder):
        self.basefolder = Path(basefolder/"dataset")
        #find