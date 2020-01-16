from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1
from reportlab.lib.units import inch

from typing import NamedTuple

class Location(NamedTuple):
    x: float
    y: float

class Font(NamedTuple):
    font_name: str
    font_size: float

class Color(NamedTuple):
    """Values between 0 and 1"""
    r: float
    g: float
    b: float

def createTrueTypeFont(font_file: str, font_name: str):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont(font_name, font_file))

def generate_label(
    canvas: canvas.Canvas,
    string: str,
    location: Location,
    font: Font,
    color: Color,
) -> None:
    canvas.setFont(font.font_name, font.font_size)
    canvas.setFillColorRGB(color.r, color.g, color.b)
    canvas.drawString(location.x, location.y, string)

def generate_label_page(
    string: str,
):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A1)
    white = Color(1, 1, 1)
    generate_label(can, string, Location(inch * 21.55, 0.1 * inch), Font("customfont", 60), white)
    can.save()
    packet.seek(0)

    label_pdf = PdfFileReader(packet)
    return label_pdf.getPage(0)

def add_label_to_file(
    original_file: str,
    new_file: str,
    label_string: str,
):
    with open(original_file, "rb") as orig, \
        open(new_file, "wb") as new:
        original_page = PdfFileReader(orig).getPage(0)
        label_page = generate_label_page(label_string)
        original_page.mergePage(label_page)

        output_pdf = PdfFileWriter()
        output_pdf.addPage(original_page)
        output_pdf.write(new)

def cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Add labels to some CMEE-Posters")
    parser.add_argument(
        "input_dir", help="The directory containing the PDFs to label")
    parser.add_argument(
        "output_dir", help="The directory to place the modified PDFs"
    )
    args = parser.parse_args()
    return main(args.input_dir, args.output_dir)

def add_label(input_file: Path, output_dir: Path):
    new_file = output_dir / input_file.name
    import re
    match = re.search(r"^([TEFWI]\d{2}).*\.pdf$", input_file.name)
    if match == None:
        raise Exception(
            f"Could not find file number in filename {input_file}."
            "It must start with a letter and two numbers, e.g. W21-somthing.pdf")
    number = match.group(1)
    add_label_to_file(str(input_file), str(new_file), str(number))

def main(input_dir: str, output_dir: str):
    createTrueTypeFont("LSANS.TTF", "customfont")

    input_dir = Path(input_dir)
    assert input_dir.is_dir()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_files = input_dir.glob("*.pdf")

    for input_file in input_files:
        add_label(input_file, output_dir)
        print(f"Done with {input_file}")

if __name__ == "__main__":
    cli()
