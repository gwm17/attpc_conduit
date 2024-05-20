import rerun.blueprint as bpt


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
                bpt.TensorView(name="2D-Histograms", contents="$origin/histograms/**"),
                bpt.TextLogView(name="Logs"),
            ),
        )
    )
