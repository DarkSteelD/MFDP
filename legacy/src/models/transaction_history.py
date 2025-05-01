from dataclasses import dataclass
from datetime import datetime
from  copy import deepcopy
@dataclass
class Transaction:
    change: int
    valid: bool
    time: datetime

class TransactionHistory:
    def __init__(self):
        self.__transaction_list = [] # later will change for db interaction

    def add_transaction(self, transaction: Transaction) -> None:
        self.__transaction_list += [transaction]
    
    def get_TransactionList(self):
        return deepcopy(self.__transaction_list)