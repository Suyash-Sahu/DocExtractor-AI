from PIL import Image


image = Image.open(
    "samples/receipt_ocr.png"
)

image.convert("RGB").save(
    "samples/receipt_scanned.pdf"
)

print("Created samples/receipt_scanned.pdf")