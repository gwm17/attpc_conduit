from spyral_utils.plot.histogram import Histogrammer
from .static import PARTICLE_ID_HISTOGRAM, KINEMATICS_HISTOGRAM, POLAR_HISTOGRAM


def init_default_histograms(grammer: Histogrammer) -> None:
    """Create the default histograms

    Creates a particle ID, kinematics, and polar angle histogram

    Parameters
    ----------
    grammer: Histogrammer
        The histogrammer which will own the histograms

    """
    grammer.add_hist2d(PARTICLE_ID_HISTOGRAM, (512, 512), ((0.0, 200.0), (0.0, 3.0)))
    grammer.add_hist2d(KINEMATICS_HISTOGRAM, (180, 512), ((0.0, 180.0), (0.0, 3.0)))
    grammer.add_hist1d(POLAR_HISTOGRAM, 180, (0, 180.0))
