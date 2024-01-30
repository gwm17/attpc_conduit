mod backend;
mod conduit;

use pyo3::prelude::*;

use conduit::Conduit;

/// The _attpc_conduit python module
#[pymodule]
fn _attpc_conduit(_py: Python, m: &PyModule) -> PyResult<()> {
    pyo3_log::init();
    m.add_class::<Conduit>()?;
    Ok(())
}
