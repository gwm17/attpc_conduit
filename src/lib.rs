mod backend;
mod conduit;

use pyo3::prelude::*;

use conduit::Conduit;

/// A Python module implemented in Rust.
#[pymodule]
fn _attpc_conduit(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Conduit>()?;
    Ok(())
}
