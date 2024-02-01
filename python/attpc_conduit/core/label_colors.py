def get_label_color(label: int) -> tuple[float, float, float, float]:
    color_label = label
    if color_label > 8:
        color_label %= 8
    match label:
        case -1:
            return (0.0, 0.0, 0.0, 0.3)  # gray
        case 0:
            return (1.0, 0.0, 0.0, 1.0)  # red
        case 1:
            return (0.0, 1.0, 0.0, 1.0)  # green
        case 2:
            return (0.0, 0.0, 1.0, 1.0)  # blue
        case 3:
            return (1.0, 1.0, 0.0, 1.0)  # yellow
        case 4:
            return (1.0, 0.0, 1.0, 1.0)  # purple
        case 5:
            return (0.0, 1.0, 1.0, 1.0)  # cyan
        case 6:
            return (0.9, 0.3, 0.1, 1.0)  # orange
        case 7:
            return (1.0, 0.2, 0.4, 0.8)  # pink
        case 8:
            return (1.0, 0.7, 0.0, 1.0)  # gold
    return (1.0, 1.0, 1.0, 1.0)  # oops you get white
