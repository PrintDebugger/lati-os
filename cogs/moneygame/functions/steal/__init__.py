import random

from ...classes import LuckHandler, MoneyItem


class StealCommand:

    @staticmethod
    def get_steal_result(stealer, victim):
        if "6" in victim.active_items:
            death_chance = random.random()
            if (death_chance > 0.75) or (not "4" in stealer.active_items and death_chance > 0.5):
                return "OTHER", {}

        if "5" in victim.active_items:
            return "FAIL_PADLOCK", {}

        chance = random.random()
        outcome = LuckHandler.get_outcome('steal', chance)
        return ("SUCCESS" if outcome.success else "FAIL"), outcome.info
    

    @staticmethod
    def generate_response(result, outcome, target, stolen_money):
        color = (
            0x70d772 
            if result == "SUCCESS"
            else 0xff61bb
        )

        if result == "SUCCESS":
            msg = outcome['message'] + f"\n* You payout was **{stolen_money:,} coins**."
        elif result == "FAIL":
            msg = (
                "Nice try lol, you got caught.\n"
                f"* You paid {target.name} **{abs(stolen_money):,} coins**"
            )
        elif result == "FAIL_PADLOCK":
            item = MoneyItem.from_id(5)
            msg = (
                f"Huh? The user has a {item.emoji} **{item.name}** on their wallet!\n"
                f"* You got caught! You paid {target.name} **{abs(stolen_money):,} coins**."
            )
        elif result == "OTHER":
            item = MoneyItem.from_id(6)
            msg = (
                f"While stealing, you stepped on the user's {item.emoji} **{item.name}** and died!\n"
                "* You lost **all of your coins**."
            )

        return msg, color
    

    @staticmethod
    def generate_dm(result, username, padlock_break=False, stolen:int=None):
        if padlock_break:
            item = MoneyItem.from_id(5)
            title = "Your padlock broke!"
            msg = f"{username} broke your {item.emoji} **{item.name}** while stealing from you!"
        elif result == "SUCCESS":
            title = "You're being robbed!"
            msg = f"Oh no! {username} stole **{stolen:,} coins** from you."
        elif result == "FAIL":
            title = "Someone tried to steal from you!"
            msg = f"{username} tried to steal from you, but failed!"
        elif result == "FAIL_PADLOCK":
            item = MoneyItem.from_id(5)
            title = "Your padlock protected you!"
            msg = f"{username} tried to steal from you, but was stopped by your {item.emoji} **{item.name}**!"
        elif result == "OTHER":
            item = MoneyItem.from_id(6)
            title = "Your bomb trap detonated!"
            msg = f"{username} tried to steal from you, but was killed by your {item.emoji} **{item.name}**!"

        return title, msg