# attpc_conduit

attpc_conduit is a Rust/Python pacakge for processing online AT-TPC data from the 
GETDAQ. The conduit uses an asynchronous backend written in Rust to recieve data from 
the GETDAQ and exposes the data to a Python analysis pipeline. Finally, the data is 
logged and viewed using the [Rerun](https://rerun.io) system.

## Install

Once it has been tested attpc_conduit will be published to PyPI and installable with 
pip.

## Manual Install

Currently attpc_conduit must be manually installed. This is handled through the 
[maturin](https://github.com/PyO3/maturin) toolchain. To use maturin, be sure to have 
the Rust toolchain installed on your machine (instructions for this can be found 
[here](https://rust-lang.org/tools/install)). Additionally, attpc_conduit requires 
Python version > 3.8, and it is recommended to use Python 3.11. Once these requirements
are satisfied, create a virtual environment for attpc_conduit and install maturin:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install maturin
```

The above example code is for Linux and MacOS where Python 3.11 is installed as 
python3.11. Once maturin is installed, the attpc_conduit package can be built and 
installed to the virtual environment using

```bash
maturin develop
```

This will build the package and install it locally. By default, the Rust side of the 
package is compiled in the release configuration. For debugging, it may be useful to 
switch to a debug build, which can be controlled by editing the appropriate section of 
the pyproject.toml.

## Use

To run attpc_conduit you must have already started the following services:

- The AT-TPC GETDAQ system, including the customized 
[DataExporter](https://github.com/gwm17/DataExporter)
- A [Rerun](https://rerun.io) viewer

There are several apporaches to using attpc_conduit, each of which exposes a different
level of control to the user. The simplest is using the default `run-conduit` command
installed with the library:

```bash
run-conduit 
```

The following options can be passed to run-conduit:

- `--viewer-ip`: The IP address of the machine running the Rerun viewer
- `--viewer-port`: The port number of the Rerun viewer

This runs a the conduit with a default analysis pipeline. In general, however, you'll
want to adjust analysis parameters or pipeline settings. Running the 
`gen-conduit-script` command

```bash
gen-conduit-script <your_script.py>
```

will generate a copy of the default script which you can edit and customize to fit the 
needs of an experiment. The analysis pipeline should be very familiar to users of 
[Spyral](https://github.com/ATTPC/Spyral).

attpc_conduit also contains an extension to the rerun file loading system, allowing for
loading AT-TPC data files. To load a merged AT-TPC HDF5 file use the following 
commandline syntax:

```bash
rerun /path/to/your/file.h5
```

Unfortunately, the analysis used by file loading is not currently modifiable, and as
such should only be used for debugging.

## How does it work?

attpc_conduit is a two-stage approach to data analysis and viewing. The first stage is 
written entirely in Rust. This stage is an asynchronous data receiving and event-building 
using [tokio](https://tokio.rs) and parts of the 
[attpc_merger](https://attpc.github.io/attpc_merger) systems. Data is imported from 
modified GET DataRouters (see [DataExporter](https://github.com/gwm17/DataExporter) for
details) and merged into events. This backend system is the actual Conduit. Using the 
amazing [PyO3](https://github.com/PyO3/pyo3) library, Python bindings are created for 
the Conduit, allowing it to be controlled from Python and for data to be transferred to
Python.

Once events are built, they are then marshalled and exposed to a Python analysis 
pipeline which contains a parsed-down set of the 
[Spyral](https://attpc.github.io/Spyral) data analysis framework, customized for online
analysis. This pipeline receives the raw events, converts them into point clouds, 
performs a clustering analysis to identify particle trajectories, and then estimates 
physical observables such as magnetic rigidity and scattering angle.

The final component of attpc_conduit is the data viewing. This is handled by the awesome
[Rerun](https://rerun.io) system. Point clouds, clusters, and observables are logged to
the Rerun system in various formats, and then can be inspected by the Rerun viewer. 
Rerun is a powerful tool that also allows for multimodal, temporal data inspection, 
which is ideal for AT-TPC data. There are still some hard edges, as Rerun is quite new, 
but it has most of the features we need already built in.

## Requirements

Rust >= 1.72
Python >= 3.10
