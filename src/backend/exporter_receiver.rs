use std::net::SocketAddr;
use tokio::io::AsyncReadExt;
use tokio::net::TcpStream;
use tokio::sync::{broadcast, mpsc};
use tokio::task::JoinHandle;
use tokio::time::timeout;

use super::constants::{
    EXPECTED_HEADER_SIZE, EXPORTER_PORT, MM_IP_SUBNET, NUMBER_OF_COBOS, SIZE_UNIT,
};
use super::error::ExporterReceiverError;
use super::graw_frame::{GrawFrame, GrawFrameHeader};
use super::message::ConduitMessage;

const CONNECTION_TIMEOUT: std::time::Duration = std::time::Duration::from_secs(120);

pub async fn run_exporter_receiver(
    ip: &str,
    port: &str,
    tx: mpsc::Sender<GrawFrame>,
    mut cancel: broadcast::Receiver<ConduitMessage>,
) -> Result<(), ExporterReceiverError> {
    let addr: SocketAddr = format!("{ip}:{port}").parse()?;
    let mut socket: TcpStream = (timeout(CONNECTION_TIMEOUT, TcpStream::connect(&addr)).await?)?;
    tracing::info!("Connected ExporterReciever to IP: {ip}");
    loop {
        tokio::select! {
            _ = cancel.recv() => {
                return Ok(());
            },
            _ = reciever_read_and_send(&mut socket, &tx) => ()
        }
    }
}

async fn reciever_read_and_send(
    socket: &mut TcpStream,
    tx: &mpsc::Sender<GrawFrame>,
) -> Result<(), ExporterReceiverError> {
    let mut header_buffer: Vec<u8> = vec![0; (EXPECTED_HEADER_SIZE as u32 * SIZE_UNIT) as usize];
    let mut frame_buffer: Vec<u8> = vec![];
    socket.read_exact(&mut header_buffer).await?;
    let header = GrawFrameHeader::from_buffer(&header_buffer)?;
    frame_buffer.resize((header.frame_size * SIZE_UNIT) as usize, 0);
    socket.read_exact(&mut frame_buffer).await?;
    let mut frame = GrawFrame::new(header);
    frame.read(frame_buffer)?;
    tx.send(frame)
        .await
        .expect("Couldn't internal send to merger from ECCReceiver");
    return Ok(());
}

/// Helper function to start and spawn all DataExporter communication tasks
pub fn startup_exporter_recievers(
    rt: &tokio::runtime::Runtime,
    frame_tx: &mpsc::Sender<GrawFrame>,
    cancel_tx: &broadcast::Sender<ConduitMessage>,
) -> Vec<JoinHandle<()>> {
    let mut handles: Vec<JoinHandle<()>> = vec![];
    tracing::info!("Connecting ECCReceivers...");
    for idx in 0..NUMBER_OF_COBOS {
        let this_frame_tx = frame_tx.clone();
        let this_cancel_rx = cancel_tx.subscribe();
        let ip = format!("{}.{}", MM_IP_SUBNET, 60 + idx);
        let handle = rt.spawn(async move {
            match run_exporter_receiver(&ip, EXPORTER_PORT, this_frame_tx, this_cancel_rx).await {
                Ok(()) => tracing::info!("Disconnected ECCReceiver from IP: {}", ip),
                Err(e) => tracing::error!("ECCReciever ran into an error: {}", e),
            }
        });

        handles.push(handle);
    }

    return handles;
}
