from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import json
import os
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader  # ✅ Added this import
from PIL import Image
from datetime import datetime

app = Flask(__name__)
DATA_FILE = os.path.join('data', 'seats.json')

# Prices
NORMAL_PRICE = 30
VIP_PRICE = 50

# Shows
SHOWS = [
    {
        "id": 1,
        "title": "Nirvaan",
        "description": "A gripping college natak.",
        "datetime": "2025-10-29 18:00",
        "image": "/static/images/nirvan.jpg"
    },
    {
        "id": 2,
        "title": "Andhagharam",
        "description": "A mysterious performance.",
        "datetime": "2025-10-29 19:00",
        "image": "/static/images/andhagharam.jpg"
    },
    {
        "id": 3,
        "title": "Umaj",
        "description": "Classic episodes on stage.",
        "datetime": "2025-10-29 20:00",
        "image": "/static/images/umaj.jpg"
    }
]


# Helpers
def load_seats():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_seats(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    now = datetime.now()
    shows = []
    for s in SHOWS:
        dt = datetime.strptime(s['datetime'], '%Y-%m-%d %H:%M')
        delta = dt - now
        shows.append({**s, 'datetime_obj': s['datetime'], 'countdown_seconds': max(int(delta.total_seconds()), 0)})
    return render_template('index.html', shows=shows)

@app.route('/show/<int:show_id>')
def show_seats(show_id):
    seats = load_seats()
    show = next((s for s in SHOWS if s['id'] == show_id), None)
    if not show:
        return "Show not found", 404
    return render_template('seats.html', show=show, seats=seats, rows=5, cols=10, vip_rows=[1], normal_price=NORMAL_PRICE, vip_price=VIP_PRICE)

@app.route('/book', methods=['POST'])
def book():
    form = request.form
    show_id = int(form.get('show_id'))
    name = form.get('name', 'Guest')
    email = form.get('email', '')
    seats_selected = form.get('seats')  # comma separated
    if not seats_selected:
        return "No seats selected", 400
    seats_list = seats_selected.split(',')

    seats = load_seats()
    for s in seats_list:
        if seats.get(s) == 'booked':
            return f"Seat {s} already booked.", 400
        seats[s] = 'booked'
    save_seats(seats)

    show = next((s for s in SHOWS if s['id'] == show_id), None)
    ticket = {
        'name': name,
        'email': email,
        'show': show,
        'seats': seats_list,
        'total': sum([VIP_PRICE if seat.startswith('A') else NORMAL_PRICE for seat in seats_list])
    }

    pdf_bytes = generate_ticket_pdf(ticket)
    return send_file(pdf_bytes, download_name='ticket.pdf', as_attachment=True)

def generate_ticket_pdf(ticket):
    qr_payload = json.dumps({'name': ticket['name'], 'show': ticket['show']['title'], 'seats': ticket['seats']})
    qr = qrcode.make(qr_payload)
    qr_io = BytesIO()
    qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    pdf_io = BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=A6)
    width, height = A6
    c.setFont('Helvetica-Bold', 12)
    c.drawString(10, height - 20, f"Rangbhumi RSCOE - {ticket['show']['title']}")
    c.setFont('Helvetica', 9)
    c.drawString(10, height - 35, f"Date/Time: {ticket['show']['datetime']}")
    c.drawString(10, height - 50, f"Name: {ticket['name']}")
    c.drawString(10, height - 65, f"Seats: {', '.join(ticket['seats'])}")
    c.drawString(10, height - 80, f"Total: Rs {ticket['total']}")

    # ✅ FIX: Wrap BytesIO in ImageReader
    qr_img = Image.open(qr_io)
    qr_w = 80
    qr_h = 80
    qr_img = qr_img.resize((qr_w, qr_h))
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    qr_image_reader = ImageReader(qr_buf)   # ✅ This is the fix
    c.drawImage(qr_image_reader, width - qr_w - 10, 10, qr_w, qr_h)

    c.showPage()
    c.save()
    pdf_io.seek(0)
    return pdf_io

if __name__ == '__main__':
    import os
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/seats.json'):
        seats = {}
        rows = ['A','B','C','D','E']
        prebooked = ['A3', 'A5', 'B7', 'C1', 'D10']
        for r in rows:
            for c in range(1, 11):
                key = f"{r}{c}"
                seats[key] = 'available'
        for p in prebooked:
            seats[p] = 'booked'
        import json
        with open('data/seats.json', 'w') as f:
            json.dump(seats, f)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
