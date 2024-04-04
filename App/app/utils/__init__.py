import json
import numpy as np


def load_config(path):
    with open(path, 'r', encoding="utf-8") as f:
        config = json.load(f)

    return config


def normalize_image(image, width, center):
    vmax = center + width // 2
    vmin = center - width // 2

    image = np.clip(image, a_min=vmin, a_max=vmax)
    image -= vmin
    image /= (vmax - vmin)

    return image
