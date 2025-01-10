use std::net::SocketAddr;
use tokio::io::AsyncReadExt;
use tokio::net::TcpStream;
use tokio::sync::{broadcast, mpsc};
use tokio::task::JoinHandle;
use tokio::time::timeout;

use super::constants::{
    EXPECTED_HEADER_SIZE, EXPORTER_PORT, MM_IP_SUBNET, NUMBER_OF_COBOS, SIZE_UNIT,
};
use super::error::{ConduitError, ExporterReceiverError};
use super::graw_frame::{GrawFrame, GrawFrameHeader};
use super::message::ConduitMessage;

/// Just to make sure we never get hung on connecting
const CONNECTION_TIMEOUT: std::time::Duration = std::time::Duration::from_secs(120);
/// Convert from GRAW size to real bytes
const HEADER_SIZE_BYTES: usize = ((EXPECTED_HEADER_SIZE as u32) * SIZE_UNIT) as usize;

/// This is the main loop of the receiver task, using a tokio::select macro to wait on
/// either data to be available on the TcpStream or a cancel message
async fn run_exporter_receiver(
    ip: &str,
    port: &str,
    tx: mpsc::Sender<GrawFrame>,
    mut cancel: broadcast::Receiver<ConduitMessage>,
) -> Result<(), ExporterReceiverError> {
    let addr: SocketAddr = format!("{ip}:{port}").parse()?;
    let mut socket: TcpStream = (timeout(CONNECTION_TIMEOUT, TcpStream::connect(&addr)).await?)?;
    loop {
        tokio::select! {
            _ = cancel.recv() => {
                return Ok(());
            },
            _ = socket.readable() => {
                if let Some(frame) = reciever_read_frame(&mut socket).await? {
                    tx.send(frame).await?;
                }
            }
        }
    }
}

/// Read a single frame off the TcpStream
async fn reciever_read_frame(
    socket: &mut TcpStream,
) -> Result<Option<GrawFrame>, ExporterReceiverError> {
    let message_size = socket.read_u64_le().await?;
    // Socket wasn't actually ready, maybe?
    if message_size == 0 {
        return Ok(None);
    }
    let mut message_buffer: Vec<u8> = vec![0; message_size as usize];
    socket.read_exact(&mut message_buffer).await?;
    let header = GrawFrameHeader::from_buffer(&message_buffer[0..HEADER_SIZE_BYTES])?;
    let mut frame = GrawFrame::new(header);
    frame.read(&message_buffer[HEADER_SIZE_BYTES..])?;
    return Ok(Some(frame));
}

/// Helper function to start and spawn all DataExporter communication tasks
pub fn startup_exporter_recievers(
    rt: &tokio::runtime::Runtime,
    frame_tx: &mpsc::Sender<GrawFrame>,
    cancel_tx: &broadcast::Sender<ConduitMessage>,
) -> Vec<JoinHandle<Result<(), ConduitError>>> {
    let mut handles = vec![];
    for idx in 0..NUMBER_OF_COBOS {
        let this_frame_tx = frame_tx.clone();
        let this_cancel_rx = cancel_tx.subscribe();
        let ip = format!("{}.{}", MM_IP_SUBNET, 60 + idx);
        let handle = rt.spawn(async move {
            match run_exporter_receiver(&ip, EXPORTER_PORT, this_frame_tx, this_cancel_rx).await {
                Ok(()) => Ok(()),
                Err(e) => Err(ConduitError::BrokenReceiver(e)),
            }
        });

        handles.push(handle);
    }

    return handles;
}
