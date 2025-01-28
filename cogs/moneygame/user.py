#   Fetch userdata through a discord user ID

from cogs.moneygame import MoneyItem
from utils import execute_query, log

class MoneyUser:
    
    def __init__(self, user_id: int): # Loads empty cache values
        self.id = user_id
        self._has_account = None
        self._wallet = None
        self._bank = None
        self._level = None
        self._exp = None
        self._items = None
                
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
    
    @property
    def items(self) -> dict:
        if self._items is None:
            data = execute_query("SELECT items from users where id = %s", (self.id,), fetch='one')
            self._items = (data[0] if data else {}) or {}
        return self._items.copy()
    
    def load_all(self):
        try:
            data = execute_query("SELECT wallet, bank, level, exp from users where id = %s", (self.id,), fetch='one')
            self._wallet, self._bank, self._level, self._exp = data
        except Exception as e:
            log(f"[{self.id}] ❌ Failed to fetch data:\n{str(e)}")

    def create_account(self):
        try:
            execute_query("INSERT INTO users (id) VALUES (%s)", (self.id,))
            self._has_account = True
            self._wallet = 10000
            self._bank = 0
            self._level = 1
            self._exp = 0
            self._items = {}
        except Exception as e:
            log(f"[{self.id}] ❌ Failed to create account:\n{str(e)}")
    
    async def add_wallet(self, amount):
        try:
            data = execute_query("UPDATE users SET wallet = wallet + %s WHERE id = %s RETURNING wallet", (amount, self.id,), fetch='one')
            self._wallet = data[0]
            old_wallet = self._wallet - amount
            log(f"[{self.id}] Updated wallet: {old_wallet} -> {self._wallet}")
        except Exception as e:
            log(f"[{self.id}] ❌ Failed to update wallet:\n{str(e)}")

    async def add_bank(self, amount):
        try:
            data = execute_query(
                "UPDATE users SET wallet = wallet - %s, bank = bank + %s WHERE id = %s RETURNING wallet, bank", 
                (amount, amount, self.id,),
                fetch='one'
            )
            self._wallet, self._bank = data
            old_wallet = self.wallet + amount
            old_bank = self.bank - amount
            log(f"[{self.id}] updated wallet: {old_wallet} -> {self._wallet}, bank: {old_bank} -> {self._bank}")
        except Exception as e:
            log(f"[{self.id}] ❌ Bank transfer failed:\n{str(e)}")
            
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

        return {
            'hasLeveledUp': level > old_level,
            'level': self.level,
            'rewards': rewards
        }
    
    def calculate_cash_multi(self):
        return 0.96 + self.level * 0.04
    
    
    async def add_item(self, item_id: int, amount: int):
        if amount == 0:
            raise ValueError("Amount cannot be zero")
        
        if MoneyItem.from_id(item_id) is None:
            raise ValueError(f"item_id {item_id} does not exist")

        try:
            updated_items = execute_query("""
                WITH current_data AS (SELECT items FROM users WHERE id = %s FOR UPDATE)
                UPDATE users SET items =
                    CASE
                        WHEN (items->>%s)::int + %s < 0 THEN
                            items               -- Prevent negative value
                        WHEN (items->>%s)::int + %s = 0 THEN
                            items - %s          -- Remove key
                        ELSE
                            jsonb_set(
                                COALESCE(items, '{}'::jsonb),
                                ARRAY[%s],
                                to_jsonb(
                                    COALESCE((items->>%s)::int, 0) + %s
                                )
                            )
                    END
                WHERE id = %s
                RETURNING COALESCE(items, '{}'::jsonb)
            """, (
                self.id,
                str(item_id), amount,
                str(item_id), amount,
                str(item_id),
                str(item_id),
                str(item_id), amount,
                self.id,
            ), fetch='one')

            #   Update cache
            self._items = updated_items[0]
            
            #   Logging
            new_item_amount = self._items[str(item_id)]
            if new_item_amount:
                log(f"[{self.id}] updated item {MoneyItem.from_id(item_id).name} (id {item_id}): {new_item_amount - amount} -> {new_item_amount}")
            else:
                log(f"[{self.id}] updated item {MoneyItem.from_id(item_id).name} (id {item_id}): {- amount} -> 0")

        except:
            log(f"[{self.id}] ❌ Failed to update item with id {item_id}")
            raise
