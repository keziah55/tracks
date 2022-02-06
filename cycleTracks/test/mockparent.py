from cycleTracks.data import CycleData, Summary
from . import makeDataFrame
import tempfile
import pandas as pd

class MockParent:
    """ Mock CycleTracks object.
    
        Data can be passed in with `dct` or a pre-determined data set can be 
        used by passing `known=True`. If neither `dct` nor `known` are passed,
        random data will be generated.
    
        Parameters
        ----------
        dct : dict, optional
            If provided, make DataFrame from this dict. Default is None, generate
            random data. See also `fixed`.
        random : bool, optional
            If True (and `dct` not supplied) generate random data. Otherwise,
            use pre-set data. Default is True.
        size : int, optional
            If generating random data, make DataFrame of this length. Default is 500.
    """
    def __init__(self, **kwargs):
        self.tmpfile = tempfile.NamedTemporaryFile()
        dct = kwargs.get('dct', None)
        random = kwargs.get('random', True)
        if dct is None:
            size = kwargs.get('size', 500)
            makeDataFrame(random=random, size=size, path=self.tmpfile.name)
        else:
            df = pd.DataFrame.from_dict(dct)
            df.to_csv(self.tmpfile.name, index=False)
        self.df = pd.read_csv(self.tmpfile.name, parse_dates=['Date'])
        self.data = CycleData(self.df)
        self.dataAnalysis = None
        self.summary = Summary()
        
