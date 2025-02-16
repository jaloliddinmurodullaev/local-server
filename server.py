from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import win32print
import win32ui
import win32con as wcon
import requests
from PIL import Image, ImageWin
import qrcode
import io

app = Flask(__name__)
CORS(app)

def json_to_receipt(content):
    receipt = []

    # Header
    receipt.append(30 * "=")
    receipt.append(f'      {content["organization"]}')
    receipt.append(30 * "=")
    receipt.append(f'Кассир: {content["cashier"]}')
    receipt.append(30 * "=")

    # Products
    for idx, product in enumerate(content["products"], start=1):
        receipt.append(f"{idx}. {product['name']}")
        receipt.append(f"   {product['count']} x {product['price']} = {product['total_price']}")
        receipt.append(30 * "-")

    # Total
    receipt.append(f"Итого к оплате: {content['total_amount']} сум")
    receipt.append(30 * "=")
    receipt.append("\n")
    receipt.append(f'      +998992747465')
    receipt.append("\n")
    receipt.append(30 * "=")

    return "\n".join(receipt)

def download_image(url):
    """ Download an image from a URL and convert it for printing """
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        img = Image.open(io.BytesIO(response.content)).convert("L")  # Convert to grayscale
        img = img.resize((250, 100))  # Resize for thermal printer
        return img
    return None

def generate_qr_code(data):
    """ Generate a QR code and return the image """
    qr = qrcode.make(data)
    return qr

def draw_img(hdc, dib, maxh, maxw):
    w, h = dib.size
    print("Image HW: ({:d}, {:d}), Max HW: ({:d}, {:d})".format(h, w, maxh, maxw))
    h = min(h, maxh)
    w = min(w, maxw)
    l = (maxw - w) // 2
    t = (maxh - h) // 2
    print(l, t, w, h)
    dib.draw(hdc, (l, t + 1000, l + w - 50, t + h + 1000))

def add_img(hdc, file_name, new_page=False):
    if new_page:
        hdc.StartPage()
    maxw = hdc.GetDeviceCaps(wcon.HORZRES)
    maxh = hdc.GetDeviceCaps(wcon.VERTRES)
    img = Image.open(file_name)
    dib = ImageWin.Dib(img)
    print(maxw, maxh)
    draw_img(hdc.GetHandleOutput(), dib, 200, 350)
    if new_page:
        hdc.EndPage()

def print_receipt(content):
    """ Print text and images using Windows thermal printer """
    printer_name = win32print.GetDefaultPrinter()
    printer_handle = win32print.OpenPrinter(printer_name)
    
    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)
    hdc.StartDoc("Receipt")
    hdc.StartPage()

    # Print Logo
    # add_img(hdc, 'logo.png', new_page=True)

    # Print Text
    y_position = 330
    line_height = 30
    hdc.SelectObject(win32ui.CreateFont({"name": "Courier New", "height": 24, "weight": 700}))

    for line in json_to_receipt(content).split("\n"):
        hdc.TextOut(10, y_position, line)
        y_position += line_height

    # Print QR Code
    add_img(hdc, 'qr.png')

    hdc.EndPage()
    hdc.EndDoc()
    hdc.DeleteDC()

@app.route('/print', methods=['POST'])
@cross_origin()
def print_content():
    content = request.json.get("content")
    if not content:
        return jsonify({"error": "No content provided"}), 400

    try:
        print_receipt(content)
        return jsonify({"message": "Receipt printed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7050)