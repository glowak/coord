import pandas as pd
import csv

from typing import Optional
from abc import ABC, abstractmethod

class Info(ABC):
    ''' 
    An abstract class representing a pandas DataFrame with information.
    '''
    def __init__(self,
                 template: Optional[pd.DataFrame] = None,
                 cols: Optional[list] = None):
        assert template is not None or cols is not None, "columns or template must be specified"
        
        if template is not None:
            self.table = pd.DataFrame(columns=template.columns)
        else:
            self.table = pd.DataFrame(columns=cols)
            
    def add_row(self,
                info: dict) -> None:
        self.table.loc[len(self.table)] = info
    
    @abstractmethod
    def export(self,
               path: str) -> None:
        pass

class CSVInfo(Info):
    '''
    A class representing a .csv document with information.
    '''
    def __init__(self, 
                 template: Optional[pd.DataFrame] = None, 
                 cols: Optional[list] = None):
        super().__init__(template, cols)

    def export(self,
               path: str) -> None:
        self.table.to_csv(path, index=False)
        
class TSVInfo(Info):
    '''
    A class representing a .tsv document with information.
    '''
    def __init__(self, 
                 template: Optional[pd.DataFrame] = None, 
                 cols: Optional[list] = None):
        super().__init__(template, cols)
    
    def export(self, 
               path: str) -> None:
        self.table.to_csv(path, sep="\t", index=False, quoting=csv.QUOTE_NONE, escapechar='\n')