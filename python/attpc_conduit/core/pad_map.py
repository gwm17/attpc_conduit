from .constants import INVALID_PAD_ID
from .hardware_id import HardwareID, generate_electronics_id
from pathlib import Path
from dataclasses import dataclass, field

PAD_ELEC_PATH = Path(__file__).parent.resolve() / "../assets/pad_elec.csv"
PAD_GEOM_PATH = Path(__file__).parent.resolve() / "../assets/pad_xy.csv"
PAD_TIME_PATH = Path(__file__).parent.resolve() / "../assets/pad_time.csv"


@dataclass
class PadData:
    """Dataclass for storing AT-TPC pad information

    Attributes
    ----------
    x: float
        The pad x-coordinates
    y: float
        The pad y-coordinates
    gain: float
        The relative pad gain
    time_offset: float
        The pad time offset due to GET electronics
    scale: float
        The pad scale (big pad or small pad)
    hardware: HardwareID
        The pad HardwareID
    """

    x: float = 0.0
    y: float = 0.0
    time_offset: float = 0.0
    hardware: HardwareID = field(default_factory=HardwareID)


class PadMap:
    """A map of pad number to PadData

    Attributes
    ----------
    map: dict[int, PadData]
        The forward map (pad number -> PadData)
    elec_map: dict[int -> int]
        Essentially a reverse map of HardwareID -> pad number

    Methods
    -------
    PadMap(geometry_path: Path, gain_path: Path, time_correction_path: Path, electronics_path: Path, scale_path: Path)
        Construct the PadMap
    load(geometry_path: Path, gain_path: Path, time_correction_path: Path, electronics_path: Path, scale_path: Path)
        load the map data
    get_pad_data(pad_number: int) -> PadData | None
        Get the PadData for a given pad. Returns None if the pad does not exist
    get_pad_from_hardware(hardware: HardwareID) -> int | None
        Get the pad number for a given HardwareID. Returns None if the HardwareID is invalid

    """

    def __init__(self):
        """Construct the PadMap

        Uses the included assets of attpc_conduit

        Returns
        -------
        PadMap
            An instance of the class
        """
        self.map: dict[int, PadData] = {}
        self.elec_map: dict[int, int] = {}
        self.load(PAD_GEOM_PATH, PAD_TIME_PATH, PAD_ELEC_PATH)

    def load(
        self,
        geometry_path: Path,
        time_correction_path: Path,
        electronics_path: Path,
    ):
        """Load the map data

        Parameters
        ----------
        geometry_path: Path
            Path to a csv file containing pad geometry
        time_correction_path: Path
            Path to a csv file containing pad time offsets
        electronics_path: Path
            Path to a csv file containing pad hardware identifiers
        """
        with open(geometry_path, "r") as geofile:
            geofile.readline()  # Remove header
            lines = geofile.readlines()
            for pad_number, line in enumerate(lines):
                entries = line.split(",")
                self.map[pad_number] = PadData(x=float(entries[0]), y=float(entries[1]))
        # TODO: This asset doesn't exist yet
        # with open(time_correction_path, "r") as timefile:
        #     timefile.readline()
        #     lines = timefile.readlines()
        #     for pad_number, line in enumerate(lines):
        #         entries = line.split(",")
        #         self.map[pad_number].time_offset = float(entries[0])

        with open(electronics_path, "r") as elecfile:
            elecfile.readline()
            lines = elecfile.readlines()
            for line in lines:
                entries = line.split(",")
                hardware = HardwareID(
                    int(entries[4]),
                    int(entries[0]),
                    int(entries[1]),
                    int(entries[2]),
                    int(entries[3]),
                )
                self.map[hardware.pad_id].hardware = hardware
                self.elec_map[generate_electronics_id(hardware)] = hardware.pad_id

    def get_pad_data(self, pad_number: int) -> PadData | None:
        """Get the PadData associated with a pad number

        Returns None if the pad number is invalid

        Parameters
        ----------
        pad_number: int
            A pad number

        Returns
        -------
        PadData | None
            The associated PadData, or None if the pad number is invalid

        """
        if (pad_number == INVALID_PAD_ID) or not (pad_number in self.map.keys()):
            return None

        return self.map[pad_number]

    def get_pad_from_hardware(self, hardware: HardwareID) -> int | None:
        """Get the pad number associated with a HardwareID

        Returns None if the HardwareID is invalid

        Parameters
        ----------
        hardware: HardwareID
            A HardwareID

        Returns
        -------
        int | None
            The associated pad number, or None if the HardwareID is invalid

        """
        key = generate_electronics_id(hardware)
        if key in self.elec_map.keys():
            return self.elec_map[generate_electronics_id(hardware)]

        return None
