#   Fetch userdata through a discord user ID
import time

from . import MoneyItem
from utils import execute_query, logger

class MoneyUser:
    
    def __init__(self, user_id: int): # Loads empty cache values
        self.id = user_id
        self._has_account = None
        self._wallet = None
        self._bank = None
        self._bank_bonus = None
        self._level = None
        self._exp = None
        self._items = None
        self._active_items = None
                
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
    def bank_bonus(self) -> int:
        if self._bank_bonus is None:
            data = execute_query("SELECT bankBonus from users where id = %s", (self.id,), fetch='one')
            self._bank_bonus = data[0] if data else 0
        return self._bank_bonus
    
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
    
    @property
    def active_items(self) -> dict:
        if self._active_items is None:
            data = execute_query("SELECT activeItems from users where id = %s", (self.id,), fetch='one')
            self._active_items = (data[0] if data else {}) or {}
        return self._active_items.copy()
    
    @property
    def coin_multi(self) -> float:
        return 0.96 + self.level * 0.04
    
    @property
    def max_bank(self) -> int:
        return int(self.level * (self.level + 1) / 2 - 1) * 256 + self.bank_bonus + 20000
    
    def load_all(self):
        try:
            data = execute_query("SELECT wallet, bank, level, exp from users where id = %s", (self.id,), fetch='one')
            self._wallet, self._bank, self._level, self._exp = data
        except Exception:
            logger.exception(f"{self.id} - Failed to fetch data")


    def create_account(self):
        try:
            execute_query("INSERT INTO users (id) VALUES (%s)", (self.id,))
            self._has_account = True
            self._wallet = 10000
            self._bank = 0
            self._level = 1
            self._exp = 0
            self._items = {}
        except Exception:
            logger.exception(f"{self.id} - Failed to create account")
    

    async def add_wallet(self, amount):
        try:
            data = execute_query("UPDATE users SET wallet = wallet + %s WHERE id = %s RETURNING wallet", (amount, self.id,), fetch='one')
            self._wallet = data[0]
            old_wallet = self._wallet - amount
            logger.info(f"{self.id} - updated wallet: {old_wallet} -> {self._wallet}")
        except Exception:
            logger.exception(f"{self.id} - Failed to update wallet")
        
        return self


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
            logger.info(f"{self.id} - updated wallet: {old_wallet} -> {self._wallet}, bank: {old_bank} -> {self._bank}")
        except Exception:
            logger.exception(f"{self.id} - Failed to update bank")

        return self

    
    async def increase_max_bank(self, amount):
        try:
            data = execute_query(
                "UPDATE users SET bankBonus = bankBonus + %s WHERE id = %s RETURNING bankBonus", 
                (amount, self.id,),
                fetch='one'
            )
            self._bank_bonus = data[0]
            logger.info(f"{self.id} - increased bank cap by {amount}")
        except Exception:
            logger.exception(f"{self.id} - Failed to increase bank cap")

        return self
            

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
            logger.info(f"{self.id} - added {amount} exp, updated wallet: {old_wallet} -> {self._wallet}")
        else:
            logger.info(f"{self.id} - added {amount} exp")

        return {
            'hasLeveledUp': level > old_level,
            'level': self.level,
            'rewards': rewards
        }

    
    async def add_item(self, item_id, amount: int):
        item_id = str(item_id)

        if amount == 0:
            raise ValueError("Amount cannot be zero")
        
        if MoneyItem.from_id(item_id) is None:
            raise ValueError(f"item_id {item_id} does not exist")

        try:
            data = execute_query("""
                WITH current_data AS (SELECT items FROM users WHERE id = %s FOR UPDATE)
                UPDATE users SET items =
                    CASE
                        WHEN (items->>%s)::int + %s < 0 THEN
                            items               -- Prevent negative value, don't change
                        WHEN (items->>%s)::int + %s = 0 THEN
                            items - %s          -- Remove key
                        ELSE
                            jsonb_set(
                                COALESCE(items, '{}'::jsonb),
                                ARRAY[%s],
                                to_jsonb(COALESCE((items->>%s)::int, 0) + %s)
                            )
                    END
                WHERE id = %s
                RETURNING COALESCE(items, '{}'::jsonb)
            """, (
                self.id,
                item_id, amount,
                item_id, amount,
                item_id,
                item_id,
                item_id, amount,
                self.id,
            ), fetch='one')

            #   Update cache
            self._items = data[0]
            
            #   Logging
            new_item_amount = self._items.get(item_id, 0)
            logger.info(f"{self.id} - updated item {MoneyItem.from_id(item_id).name} (id {item_id}): {new_item_amount - amount} -> {new_item_amount}")

        except Exception:
            logger.exception(f"{self.id} - Failed to update item with id {item_id}")
            raise

        return self

    
    async def activate_item(self, item_id, duration: int):
        item_id = str(item_id)

        if duration <= 0:
            raise ValueError("duration must be a positive integer")
        
        try:
            data = execute_query("""
                UPDATE users SET activeItems = jsonb_set(
                    COALESCE(activeItems, '{}'::jsonb),
                    ARRAY[%s],
                    to_jsonb(COALESCE((activeItems->>%s)::int, %s) + %s)
                ) 
                WHERE id = %s
                RETURNING COALESCE(activeItems, '{}'::jsonb)
                """, (
                    item_id,
                    item_id, int(time.time()), duration,
                    self.id,
                ), fetch = 'one')
            
            # Update cache
            self._active_items = data[0]

            end_time = self._active_items[item_id]
            logger.info(f"{self.id} - Activated item {MoneyItem.from_id(item_id).name} (id {item_id}) ending at {end_time}")
        except Exception:
            logger.exception(f"Failed to activate item with id {item_id}")

        return self


    async def deactivate_item(self, item_id):
        item_id = str(item_id)

        if not item_id in self._active_items:
            raise ValueError(f"{item_id} was never activated")
        
        try:
            data = execute_query("""
                    UPDATE users SET activeItems = activeItems - %s
                    WHERE id = %s
                    RETURNING COALESCE(activeItems, '{}'::jsonb)
                """, (
                    item_id,
                    self.id,
                ), fetch = 'one')
            
            # Update cache
            self._active_items = data[0]

            logger.info(f"{self.id} - Deactivated item {MoneyItem.from_id(item_id).name} (id {item_id})")
        except Exception:
            logger.exception(f"Failed to deactivate item with id {item_id}")

        return self