from importlib.resources import files, as_file

UNSIGNED_NOISE_LABEL = 4096

RADIUS = 2.0

PAD_ELEC_PATH = as_file(files("spyral.data").joinpath("pad_electronics.csv"))

PARTICLE_ID_HISTOGRAM: str = "particle_id"
KINEMATICS_HISTOGRAM: str = "kinematics"
POLAR_HISTOGRAM: str = "polar_angle"
