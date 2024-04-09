import rerun.blueprint as bpt


def generate_default_blueprint() -> bpt.Blueprint:

    return bpt.Blueprint(
        bpt.Horizontal(
            bpt.Tabs(
                bpt.Spatial2DView(name="Pad Plane"), bpt.Spatial3DView(name="Detector")
            ),
            bpt.Tabs(
                bpt.BarChartView(name="1D-Histograms"),
                bpt.TensorView(name="2D-Histograms"),
                bpt.TextLogView(name="Logs"),
            ),
        )
    )
