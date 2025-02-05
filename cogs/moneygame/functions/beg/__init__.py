import random
from ...config import PATH_BEGMSG


class BegCommand:

    @staticmethod
    def get_random_message():
        with open(PATH_BEGMSG, 'r', encoding="utf-8") as file:
            for idx, line in enumerate(file, start=1):
                if random.randint(1, idx) == 1:
                    chosen_line = line.strip()

        return chosen_line