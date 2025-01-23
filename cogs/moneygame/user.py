#   Fetch userdata through a discord user ID

from utils import execute_query, log

class UserData:
    
    def __init__(self, user_id: int):
        self.id = user_id
        self._has_account = None
        self._wallet = None
        self._bank = None
        self._level = None
        self._exp = None
                
    @property
    def has_account(self) -> bool:
        if self._has_account is None:
            data = execute_query("SELECT 1 from users where id = %s", (self.id,), fetch='one')
            self._has_account = data is not None
        return self._has_account
    
    @property
    def wallet(self) -> int:
        if self._wallet is None:
            data = execute_query("SELECT wallet from users where id = %s", (self.id,), fetch='one')
            self._wallet = data[0] if data else 10000
        return self._wallet
    
    @property
    def bank(self) -> int:
        if self._bank is None:
            data = execute_query("SELECT bank from users where id = %s", (self.id,), fetch='one')
            self._bank = data[0] if data else 0
        return self._bank
    
    @property
    def level(self) -> int:
        if self._level is None:
            data = execute_query("SELECT level from users where id = %s", (self.id,), fetch='one')
            self._level = data[0] if data else 1
        return self._level
    
    @property
    def exp(self) -> int:
        if self._exp is None:
            data = execute_query("SELECT exp from users where id = %s", (self.id,), fetch='one')
            self._exp = data[0] if data else 0
        return self._exp
    
    def load_all(self):
        try:
            data = execute_query("SELECT wallet, bank, level, exp from users where id = %s", (self.id,), fetch='one')
            self._wallet, self._bank, self._level, self._exp = data
        except Exception as e:
            log(f"[{self.id}] ❌ ERROR: Failed to fetch data:\n{str(e)}")

    def create_account(self):
        try:
            execute_query("INSERT INTO users (id) VALUES (%s)", (self.id,))
            self._has_account = True
            self._wallet = 10000
        except Exception as e:
            log(f"[{self.id}] ❌ ERROR: Failed to create account:\n{str(e)}")

    
    async def add_wallet(self, amount):
        try:
            data = execute_query("UPDATE users SET wallet = wallet + %s WHERE id = %s RETURNING wallet", (amount, self.id,), fetch='one')
            self._wallet = data[0]
            old_wallet = self._wallet - amount
            log(f"[{self.id}] Updated wallet: {old_wallet} -> {self._wallet}")
        except Exception as e:
            log(f"[{self.id}] ❌ ERROR: Failed to update wallet:\n{str(e)}")

    async def add_bank(self, amount):
        try:
            data = execute_query(
                "UPDATE users SET wallet = wallet - %s, bank = bank + %s WHERE id = %s RETURNING wallet, bank", 
                (amount, amount, self.id,),
                fetch='one'
            )
            self._wallet, self._bank = data
            old_wallet = self._wallet + amount
            old_bank = self._bank - amount
            log(f"[{self.id}] updated wallet: {old_wallet} -> {self._wallet}, bank: {old_bank} -> {self._bank}")
        except Exception as e:
            log(f"[{self.id}] ❌ ERROR: Bank transfer failed:\n{str(e)}")
            
    async def add_exp(self, amount):
        data = execute_query("SELECT wallet, level, exp FROM users WHERE id = %s FOR UPDATE", (self.id,), fetch='one')
        old_wallet, level, exp = data
        old_level = level   #   Note the user's old level to check if user has leveled up
        exp += amount
        rewards = 0

        while exp >= 25 * (level + 1):
            exp -= 25 * (level + 1)
            level += 1

            # Money rewards
            if level % 5 == 0:
                rewards += 1000 * int(3 * (level / 5) ** 1.5)

        execute_query(
            "UPDATE users SET wallet = wallet + %s, level = %s, exp = %s where id = %s", 
            (rewards, level, exp, self.id,)
        )
        self._wallet = old_wallet + rewards
        self._level = level
        self._exp = exp

        if rewards > 0:
            log(f"[{self.id}] added {amount} exp, updated wallet: {old_wallet} -> {self._wallet}")
        else:
            log(f"[{self.id}] added {amount} exp")

        level_up = level > old_level
        return {
            'hasLeveledUp': level_up,
            'level': self._level,
            'rewards': rewards
        }
    
    def calculate_cash_multi(self):
        return 0.96 + self.level * 0.04