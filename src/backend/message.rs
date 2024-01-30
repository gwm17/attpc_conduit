/// Messages the Conduit can send to the backend. For now just Cancel
#[derive(Debug, Clone)]
pub enum ConduitMessage {
    Cancel,
}
