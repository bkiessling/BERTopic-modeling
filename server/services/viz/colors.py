"""Stable categorical colors keyed by topic ID, with no six-color cycling."""

import colorsys
from plotly.colors import qualitative


def topic_colors(topics):
    palette = qualitative.Alphabet
    colors = {}
    used = set()
    for topic in sorted(set(int(value) for value in topics)):
        if topic == -1:
            color = "#8A94A6"
        elif 0 <= topic < len(palette):
            color = palette[topic]
        else:
            hue = (topic * 137.507764) % 360
            while True:
                rgb = colorsys.hls_to_rgb(hue / 360, 0.43, 0.65)
                color = "#" + "".join(f"{round(channel * 255):02X}" for channel in rgb)
                if color not in used:
                    break
                hue = (hue + 0.1) % 360
        colors[topic] = color
        used.add(color)
    return colors
