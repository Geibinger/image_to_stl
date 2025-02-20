# PNG to STL Converter

This Python script converts a PNG image into a closed STL mesh. It supports two modes:

1. **Continuous mode (default):**  
   The image is processed in grayscale. Each pixel's brightness is mapped linearly to a height (from 0 to the given extrude_height). A continuous top surface is produced along with side walls and a bottom face.

2. **Binary mode:**  
   Activate this mode with the `--binary` flag. The image is treated as black-and-white using a threshold (default 128). Pixels with values below the threshold (black) are extruded (to extrude_height) while white regions are omitted. Side walls are only added along edges bordering non-solid (white) areas so that the space between the black spots is not connected.

## Requirements

- Python 3.x
- [Pillow](https://pypi.org/project/Pillow/)
- [numpy](https://pypi.org/project/numpy/)

## Setup

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install the required packages:**

   Create a `requirements.txt` file with the following content:
   ```
   Pillow
   numpy
   ```
   Then run:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line as follows:

### Continuous Mode (Default)
```bash
python png_to_stl.py input.png output.stl --extrude_height 15.0 --x_size 120.0 --y_size 120.0
```

### Binary Mode (For QR Codes or similar)
```bash
python png_to_stl.py input.png output.stl --extrude_height 15.0 --x_size 120.0 --y_size 120.0 --binary --threshold 128
```

- **input.png:** Path to your input PNG image.
- **output.stl:** Desired path for the generated STL file.
- **--extrude_height:** Extrusion height for the solid (black) regions.
- **--x_size / --y_size:** Overall dimensions (width and depth) of the output STL.
- **--binary:** Activate binary mode.
- **--threshold:** Pixel threshold for binary mode (default: 128). Pixels with values below this are treated as solid.

## Notes

- In **continuous mode**, the entire image is used to generate a relief model.
- In **binary mode**, only regions defined as solid (black) are extruded and receive side walls, so the white areas remain unmeshed (i.e. not connected).
- The resulting STL is written as an ASCII file.

Happy 3D printing!