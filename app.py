import os
import qrcode

QR_PATH = "static/qr_math1.png"

def generate_qr():
    # URL publique Replit (mise automatiquement par toi)
    base_url = os.getenv("REPLIT_URL")   # ex: "https://presenceapp.moham.repl.co"

    if not base_url:
        print("⚠️  Variable REPLIT_URL non définie. Mettre l'URL dans les secrets.")
        return

    url = base_url + "/scan?cours=math1"

    os.makedirs("static", exist_ok=True)
    img = qrcode.make(url)
    img.save(QR_PATH)
    print("QR généré :", QR_PATH)
