import numpy as np
from importlib.resources import files, as_file

NOISE_LABEL = -1

N_CIRCLE_POINTS_RENDER = 100

CIRCLE_POLARS = np.linspace(0.0, np.pi * 2.0, N_CIRCLE_POINTS_RENDER)

RADIUS = 2.0

PAD_ELEC_PATH = as_file(files("spyral.data").joinpath("pad_electronics.csv"))
