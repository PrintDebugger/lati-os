import logging


logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


PBAR_SKINS = {
    "gold": [
        "<:Abar0:1331179174781653043>",
        "<:Abar1:1331179214719684608>",
        "<:Abar2:1331179216531886121>",
        "<:Abar3:1331179218213670942>",
        "<:Abar4:1331179220054839357>",
        "<:AbarL:1331179222047395930>",
        "<:AbarR:1331180442233077780>"
    ],
    "silver-blue": [
        "<:Bbar0:1334148298113683487>",
        "<:Bbar1:1334148300273614908>",
        "<:Bbar2:1334148302534348861>",
        "<:Bbar3:1334148304937943131>",
        "<:Bbar4:1334148306724716627>",
        "<:BbarL:1334148295676919880>",
        "<:BbarR:1334148308704165888>"
    ]
}

def progress_bar(progress:float, length:int, style:str="silver-blue"):
    """Generate a progress bar based on a float between 0 and 1"""
    segments = 4
    skin = PBAR_SKINS[style]
    segment_states = skin[:4]

    bar = skin[-2]
    bar += skin[4] * int(progress * length // 1)
    bar += segment_states[int((progress * length * segments) % segments)]
    bar += skin[0] * int((1 - progress) * length // 1)
    bar += skin[-1]
    return bar