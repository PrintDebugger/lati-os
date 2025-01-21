#   Fetch user data through a discord user ID

from utils import execute_query, log

class UserData:
    def __init__(self, user):
        self.id = user.id
        self.name = user.display_name
        self.load_data()
        
    def load_data(self):
        data = execute_query("SELECT name, wallet, bank, level, exp FROM users WHERE id = %s", (self.id,), fetch='one')

        if data:
            self.has_account = True
            self.name, self.wallet, self.bank, self.level, self.exp = data[0:]
            self.cash_multi = 0.96 + self.level * 0.04 
        else:
            self.has_account = False
            
    def create_account(self):
        execute_query("INSERT INTO users (id, name) VALUES (%s, %s)", (self.id, self.name,))
        self.has_account = True
    
    async def add_wallet(self, amount):
        self.load_data()
        old_wallet = self.wallet
        self.wallet += amount
        execute_query("UPDATE users SET wallet = %s WHERE id = %s", (self.wallet, self.id,))
        log(f"[{self.id}] updated wallet: {old_wallet} -> {self.wallet}")

    async def add_bank(self, amount):
        self.load_data()
        old_wallet = self.wallet
        old_bank = self.bank
        
        if amount > self.wallet or (self.bank + amount) < 0:
            raise ValueError("Invalid Value")
        
        self.wallet -= amount
        self.bank += amount
        execute_query("UPDATE users SET wallet = %s, bank = %s WHERE id = %s", (self.wallet, self.bank, self.id,))
        log(f"[{self.id}] updated wallet: {old_wallet} -> {self.wallet}, bank: {old_bank} -> {self.bank}")
            
    async def add_exp(self, amount, ctx):
        old_level = self.level
        self.exp += amount
        rewards = 0

        while self.exp >= 25 * (self.level + 1):
            self.exp -= 25 * (self.level + 1)
            self.level += 1

            # Money rewards
            if self.level % 5 == 0:
                rewards += 1000 * int(3 * (self.level / 5) ** 1.5)

        self.wallet += rewards
        execute_query(
            "UPDATE users SET wallet = %s, level = %s, exp = %s where id = %s", 
            (self.wallet, self.level, self.exp, self.id,)
        )

        if self.level > old_level:    
            if rewards == 0:
                await ctx.followup.send("{0} You are now Level {1}!".format(ctx.user.mention, self.level))
            else:
                await ctx.followup.send("{0} Great job on reaching level {1}! You earned ${2}".format(ctx.user.mention, self.level, rewards))
        log(f"[{self.id}] Added {amount} exp")