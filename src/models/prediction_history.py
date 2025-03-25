from copy import deepcopy
from dataclasses import dataclass

@dataclass
class Prediction:
    input_data : tuple
    output_data: tuple
    successful: bool


class Prediction_History:
    def __init__(self):
        self.__prediction_list = [] # later will change for db interaction

    def add_transaction(self, transaction: Prediction) -> None:
        self.__prediction_list += [transaction]
    
    def get_TransactionList(self):
        return deepcopy(self.__prediction_list)   