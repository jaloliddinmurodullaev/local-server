from flask import Flask, request, jsonify
import win32print
import win32ui

app = Flask(__name__)

def print_receipt(content):
    # Get the default printer name
    printer_name = win32print.GetDefaultPrinter()

    # Open the printer
    printer_handle = win32print.OpenPrinter(printer_name)
    printer_info = win32print.GetPrinter(printer_handle, 2)
    
    # Set up the device context
    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)
    hdc.StartDoc("Receipt")  # Start a new print job
    hdc.StartPage()  # Start a new page

    # Set font and size
    hdc.SelectObject(win32ui.CreateFont({
        "name": "Arial",
        "height": 30,
        "weight": 700
    }))

    # Print the content (this is for text printing)
    # hdc.TextOut(100, 100, content)
    y_position = 100
    line_height = 30
    for line in content.split("\n"):
        hdc.TextOut(-35, y_position, line)
        y_position += line_height

    # End the page and the document
    hdc.EndPage()
    hdc.EndDoc()
    hdc.DeleteDC()

# Content to print
# content = """
#     Xadecha Parfume\n
#     Receipt:\n
#     Item 1: $10\n
#     Item 2: $5\n
#     Total: $15\n
#     Xaridingiz uchun rahmat!\n\n
# """

# print_receipt(content)

@app.route('/print', methods=['POST'])
def print_content():
    # Get the content to be printed from the request body
    content = request.json.get("content")

    if not content:
        return jsonify({"error": "No content provided"}), 400

    # Call the print function
    try:
        print_receipt(content)
        return jsonify({"message": "Receipt printed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)