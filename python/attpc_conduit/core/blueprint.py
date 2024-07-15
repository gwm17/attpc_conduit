import rerun.blueprint as bpt
import rerun as rr


def generate_default_blueprint() -> bpt.Blueprint:

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
                    contents="$origin/histograms/kinematics",
                    view_fit="fill",
                    slice_selection=bpt.TensorSliceSelection(
                        width=rr.TensorDimensionSelection(dimension=1, invert=False),
                        height=rr.TensorDimensionSelection(dimension=0, invert=True),
                    ),
                ),
                bpt.TensorView(
                    name="Particle ID",
                    contents="$origin/histograms/particle_id",
                    view_fit="fill",
                    slice_selection=bpt.TensorSliceSelection(
                        width=rr.TensorDimensionSelection(dimension=1, invert=False),
                        height=rr.TensorDimensionSelection(dimension=0, invert=True),
                    ),
                ),
                bpt.TextLogView(name="Logs"),
            ),
        )
    )
