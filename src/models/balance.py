class Balance:
    def __init__(self):
        self.__balance : int = 0
    
    def update_balance(self, change: int):
        self.__balance += change
        return int(self.__balance)