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
        self.__TransactionList = [] # later will change for db interaction

    def add_transaction(self, transaction: Transaction) -> None:
        self.__TransactionList += [Transaction]
    
    def get_TransactionList(self):
        return deepcopy(self.__TransactionList)