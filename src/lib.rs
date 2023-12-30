mod backend;

use pyo3::prelude::*;

use backend::conduit::Conduit;

/// A Python module implemented in Rust.
#[pymodule]
fn attpc_conduit(_py: Python, m: &PyModule) -> PyResult<()> {
    // m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    m.add_class::<Conduit>()?;
    Ok(())
}
