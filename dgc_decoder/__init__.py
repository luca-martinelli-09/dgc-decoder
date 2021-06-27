import cbor2
import zlib
import base45
from cose.messages import CoseMessage
import json
import requests as req
import jsonschema
from pyzbar.pyzbar import decode
import cv2
import argparse
import os

args_parser = argparse.ArgumentParser(
    description="Download multiple files (serie's episodes or movies) using youtube-dl")
args_parser.add_argument("-i", "--image", dest="qr_image",
                        help="Image of QR code")
args_parser.add_argument("-q", "--qrcode", dest="barcode",
                        help="QR code decoded string")

args = args_parser.parse_args()


def load_image(qr_image):
    try:
        if os.path.isfile(qr_image):
            image = cv2.imread(qr_image)
        else:
            return None
    except:
        return None

    for qr_code in decode(image):
        return qr_code.data.decode()

    return None


def validate_certificate(cert_data):
    json_schema = json.loads(req.get(
        "https://raw.githubusercontent.com/ehn-dcc-development/ehn-dcc-schema/release/1.3.0/DCC.combined-schema.json").text)

    try:
        jsonschema.validate(instance=cert_data, schema=json_schema)
    except:
        return False

    return True


def clean_cert(cert_data):
    data = cert_data.copy()

    try:
        for key in data[-260][1]:
            data[key] = data[-260][1][key]
        del data[-260]
    except:
        pass

    return data


def decode_barcode(barcode):
    if barcode.startswith("HC1:"):
        barcode = barcode[4:]

    try:
        barcode_decoded = base45.b45decode(barcode)
        barcode_decompressed = zlib.decompress(barcode_decoded)
        barcode_cose_decoded = CoseMessage.decode(barcode_decompressed)
        barcode_data = cbor2.loads(barcode_cose_decoded.payload)
    except:
        return None

    return barcode_data


def main():
    global args

    if not args.qr_image is None:
        barcode = load_image(args.qr_image)

        if barcode is None:
            print("🛑 Invalid input")
            quit()

    elif not args.barcode is None:
        barcode = args.barcode
    else:
        print("🛑 Invalid arguments")
        quit()

    barcode_data = decode_barcode(barcode)

    if barcode_data is None:
        print("🛑 Invalid QR/Data")
        quit()

    cert_data = clean_cert(barcode_data)

    if validate_certificate(cert_data):
        print("✔️ Certificate decoded")
        print(json.dumps(cert_data, indent=2))
    else:
        print("🛑 Invalid certificate")
