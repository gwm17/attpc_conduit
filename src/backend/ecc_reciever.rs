use std::net::SocketAddr;
use tokio::io::AsyncReadExt;
use tokio::net::TcpStream;
use tokio::sync::{broadcast, mpsc};
use tokio::task::JoinHandle;
use tokio::time::timeout;

use super::constants::{EXPECTED_HEADER_SIZE, NUMBER_OF_COBOS, SIZE_UNIT};
use super::error::ECCReceiverError;
use super::graw_frame::{GrawFrame, GrawFrameHeader};
use super::message::ConduitMessage;

const CONNECTION_TIMEOUT: std::time::Duration = std::time::Duration::from_secs(120);

/// ECCReceiver is an async task which receives data from a modified GETDAQ DataRouter
/// in the form of GRAW Frames. The frames are then submitted to the EventBuilder.
#[derive(Debug)]
#[allow(dead_code)]
pub struct ECCReceiver {
    addr: SocketAddr,
    socket: TcpStream,
    transmitter: mpsc::Sender<GrawFrame>,
}

impl ECCReceiver {
    /// Create a receiver at an ip:port
    pub async fn new(
        ip: &str,
        port: &str,
        tx: mpsc::Sender<GrawFrame>,
    ) -> Result<Self, ECCReceiverError> {
        let addr: SocketAddr = format!("{ip}:{port}").parse()?;
        let socket: TcpStream = (timeout(CONNECTION_TIMEOUT, TcpStream::connect(&addr)).await?)?;
        return Ok(ECCReceiver {
            addr,
            socket,
            transmitter: tx,
        });
    }

    /// The primary task of the ECCReceiver which is spawned.
    pub async fn run(
        &mut self,
        cancel: &mut broadcast::Receiver<ConduitMessage>,
    ) -> Result<(), ECCReceiverError> {
        loop {
            tokio::select! {
                _ = cancel.recv() => {
                    return Ok(());
                },
                _ = self.read_and_send() => ()
            }
        }
    }

    /// Read in the raw GETDAQ data and convert it into a GrawFrame
    async fn read_and_send(&mut self) -> Result<(), ECCReceiverError> {
        let mut header_buffer: Vec<u8> =
            vec![0; (EXPECTED_HEADER_SIZE as u32 * SIZE_UNIT) as usize];
        let mut frame_buffer: Vec<u8> = vec![];
        self.socket.read_exact(&mut header_buffer).await?;
        let header = GrawFrameHeader::from_buffer(&header_buffer)?;
        frame_buffer.resize((header.frame_size * SIZE_UNIT) as usize, 0);
        self.socket.read_exact(&mut frame_buffer).await?;
        let mut frame = GrawFrame::new(header);
        frame.read(frame_buffer)?;
        self.transmitter
            .send(frame)
            .await
            .expect("Couldn't internal send to merger from ECCReceiver");
        return Ok(());
    }
}

/// Helper function to start and spawn all ECCReceivers
pub fn startup_ecc_recievers(
    rt: &tokio::runtime::Runtime,
    frame_tx: &mpsc::Sender<GrawFrame>,
    cancel_tx: &broadcast::Sender<ConduitMessage>,
) -> Vec<JoinHandle<()>> {
    let mut handles: Vec<JoinHandle<()>> = vec![];

    for _ in 0..NUMBER_OF_COBOS {
        let this_frame_tx = frame_tx.clone();
        let mut this_cancel_rx = cancel_tx.subscribe();
        let handle = rt.spawn(async move {
            match ECCReceiver::new("127.0.0.1", "8080", this_frame_tx).await {
                //TODO: replace these with real ip/port handlers
                Ok(mut ecc) => match ecc.run(&mut this_cancel_rx).await {
                    Ok(()) => (),
                    Err(e) => tracing::error!("ECCReciever ran into an error: {}", e),
                },
                Err(e) => tracing::error!("Could not startup ECCReciever: {}", e),
            }
        });

        handles.push(handle);
    }

    return handles;
}
