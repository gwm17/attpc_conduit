import rerun.blueprint as bpt
import rerun as rr
from .static import PARTICLE_ID_HISTOGRAM, KINEMATICS_HISTOGRAM


def generate_default_blueprint() -> bpt.Blueprint:
    """Generate a default blueprint for Rerun

    Create our normal setup, with a tab for the 3-D view,
    1-D Histograms, 2-D Histograms, and logs.

    Returns
    -------
    rerun.blueprint.Blueprint
        The rerun Blueprint
    """
    return bpt.Blueprint(
        bpt.Horizontal(
            bpt.Tabs(
                bpt.Spatial3DView(
                    name="Detector", contents=["/event/**", "/bounds/**"]
                ),
                bpt.BarChartView(
                    name="1D-Histograms", contents="$origin/histograms/**"
                ),
                bpt.TensorView(
                    name="Kinematics",
                    contents=f"$origin/histograms/{KINEMATICS_HISTOGRAM}",
                    view_fit="fill",
                    slice_selection=bpt.TensorSliceSelection(
                        width=rr.TensorDimensionSelection(dimension=0, invert=False),
                        height=rr.TensorDimensionSelection(dimension=1, invert=True),
                    ),
                ),
                bpt.TensorView(
                    name="Particle ID",
                    contents=f"$origin/histograms/{PARTICLE_ID_HISTOGRAM}",
                    view_fit="fill",
                    slice_selection=bpt.TensorSliceSelection(
                        width=rr.TensorDimensionSelection(dimension=0, invert=False),
                        height=rr.TensorDimensionSelection(dimension=1, invert=True),
                    ),
                ),
                bpt.TextLogView(name="Logs"),
            ),
        )
    )
