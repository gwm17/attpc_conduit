/// This was created to handle marshalling data from Python
/// back to Rust after basic analysis. With the addition of the
/// RerunSDK this is mostly superfulous, but keep it for now just in
/// case
#[derive(Debug, Clone)]
pub struct PointCloud {
    size_bytes: u64,
    buffer: Vec<u8>,
}

impl PointCloud {
    pub fn new(buffer: Vec<u8>) -> Self {
        PointCloud {
            size_bytes: buffer.len() as u64,
            buffer,
        }
    }
}

impl Into<Vec<u8>> for PointCloud {
    fn into(self) -> Vec<u8> {
        let mut full_buf = Vec::from(self.size_bytes.to_le_bytes());
        full_buf.extend(self.buffer.iter());
        return full_buf;
    }
}
