# attpc_conduit

attpc_conduit is a Rust/Python pacakge for processing online AT-TPC data from the GET DAQ. The conduit uses an asynchronous backend written in Rust to recieve data from the GET DAQ and exposes the data to a Python analysis pipeline. Finally, the data is logged and viewed using the [Rerun](https://rerun.io) system.

## Install

Once it has been tested attpc_conduit will be published to PyPI and installable with pip and pipx.

## Manual Install

Currently attpc_conduit must be manually installed. This is handled through the [maturin](https://github.com/PyO3/maturin) toolchain. To use maturin, be sure to have the Rust toolchain installed on your machine (instructions for this can be found [here](https://rust-lang.org/tools/install)). Additionally, attpc_conduit requires Python version > 3.8, and it is recommended to use Python 3.11. Once these requirements are satisfied, create a virtual environment for attpc_conduit and install maturin:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install maturin
```

The above example code is for Linux and MacOS where Python 3.11 is installed as python3.11. Once maturin is installed, the attpc_conduit package can be built and installed to the virtual environment using

```bash
maturin develop
```

This will build the package and install it locally. By default, the Rust side of the package is compiled in the release configuration. For debugging, it may be useful to switch to a debug build, which can be controlled by editing the appropriate section of the pyproject.toml.

## Use

To launch attpc_conduit, use the following command:

```bash
run-conduit
```

Note that the virutal environment containing attpc_conduit must be active to run this command. This will launch the Conduit control panel as well as a rerun viewer. attpc_conduit also contains an extension to the rerun file loading system, allowing for loading AT-TPC data files. To load a merged AT-TPC HDF5 file use the following commandline syntax:

```bash
rerun /path/to/your/file.h5
```

Alternatively, you can also use the Open dialog from the rerun viewer. Again, the conduit virtual environment must be active for this to work. Additionally, you must have a saved conduit configuration named "config.json" saved from wherever you launch the Rerun viewer.

## How does it work?

attpc_conduit is a two-stage approach to data analysis and viewing. The first stage is written entirely in Rust. This stage is an asynchronous data receiving and sorting using [tokio](https://tokio.rs) and parts of the [attpc_merger](https://attpc.github.io/attpc_merger) systems. Data is imported from modified GET DataRouters (see [DataExporter](https://github.com/gwm17/DataExporter) for details) and merged into events. This backend system is the actual Conduit. Using the amazing [PyO3](https://github.com/PyO3/pyo3) library, Python bindings are created for the Conduit, allowing it to be controlled from Python and for data to be transferred to Python.

Once events are built, they are then marshalled and exposed to a Python analysis pipeline which contains a parsed-down set of the [Spyral](https://attpc.github.io/Spyral) data analysis framework, customized for online analysis. This pipeline receives the raw events, converts them into point clouds, performs a clustering analysis to identify particle trajectories, and then estimates physical observables such as magnetic rigidity and scattering angle.

The final component of attpc_conduit is the data viewing. This is handled by the awesome [Rerun](https://rerun.io) system. Point clouds, clusters, and observables are logged to the Rerun system in various formats, and then can be inspected by the Rerun viewer. Rerun is a powerful tool that also allows for multimodal, temporal data inspection, which is ideal for AT-TPC data. There are still some hard edges, as Rerun is quite new, but it has most of the features we need already built in.

attpc_conduit also uses the excellent [DearPyGui](https://github.com/hoffstadt/DearPyGui) UI system to make a custom control panel for the conduit itself. This allows users to specify and control the conduit from a simple and easy to modify user interface.

## Requirements

Rust >= 1.72
Python >= 3.8
