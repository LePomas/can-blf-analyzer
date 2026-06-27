# CAN BLF Analyzer

Processes automotive BLF (Binary Logging File) recordings to extract ECU system state timelines, calculate state durations, detect off-time gaps, and count drive cycles — then exports results to Excel and JPEG.

Built for automotive/embedded validation workflows where CAN traces need to be summarized quickly without opening Vector CANalyzer.

## Features

- Batch-processes all `.blf` files in the current directory
- Extracts `SystemState` and `SupplyVoltage` signals via DBC decoding
- Collapses consecutive identical states and calculates durations
- Detects off-time gaps (> 2 s between states)
- Counts drive cycles (state 5 / DriveUp, duration > 800 s) across files
- Exports summary table to `.xlsx` and `.jpeg` per file
- Human-readable state labels (e.g. `5: DriveUp`, `8: Error`)

## Requirements

- Python 3.8+
- A `dbc/` folder containing the relevant DBC file(s)

## Installation

```sh
pip install -r requirements.txt
```

## Usage

1. Place `.blf` files and the `dbc/` folder in the same directory.
2. Run:

```sh
python blf_analyzer.py
```

Results are saved alongside the input files as `<filename>.xlsx` and `<filename>.jpeg`.

### Filtering

Open `blf_analyzer.py` and uncomment lines in `read_and_filter()` to activate signal-level filters:

```python
# df = df[df['SystemState_xdu8'] != 0]
# df = df[df['SupplyVoltage_xdu16'] <= 18.0]
# df = df[df['SupplyVoltage_xdu16'] > 0]
```

## Tech Stack

`python-can` · `candas` · `pandas` · `matplotlib` · `openpyxl`

## License

MIT
