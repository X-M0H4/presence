import os
import sqlite3
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import qrcode
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
CORS(app)

QR_PATH = "static/qr_math1.png"
DB_PATH = "database.db"

# Thread-safe initialization
_db_initialized = False
_db_init_lock = threading.Lock()

# Coordonnées de référence (salle de classe)
# À modifier selon votre localisation
REF_LAT = 48.8566  # Exemple: Paris
REF_LON = 2.3522
MAX_DISTANCE_M = 50  # Distance maximale autorisée en mètres

def init_db():
    """Initialiser la base de données si elle n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Table étudiants
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        identifier TEXT UNIQUE
    )''')
    
    # Table présences
    c.execute('''CREATE TABLE IF NOT EXISTS presences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        name TEXT,
        cours TEXT,
        timestamp TEXT,
        latitude REAL,
        longitude REAL,
        distance REAL,
        status TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')
    
    conn.commit()
    conn.close()

def get_db():
    """Connexion à la base de données SQLite avec initialisation thread-safe"""
    global _db_initialized
    
    # Double-checked locking pour thread safety
    if not _db_initialized:
        with _db_init_lock:
            if not _db_initialized:
                init_db()
                _db_initialized = True
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcule la distance en mètres entre deux points GPS"""
    R = 6371000  # Rayon de la Terre en mètres
    
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

def generate_qr():
    """Génère un QR code pour le lien de présence"""
    base_url = os.getenv("REPLIT_URL") or "http://localhost:5000"
    
    if not os.getenv("REPLIT_URL"):
        print("⚠️  Variable REPLIT_URL non définie. Utilisation de localhost.")
    
    url = base_url + "/scan?cours=math1"
    
    os.makedirs("static", exist_ok=True)
    img = qrcode.make(url)
    img.save(QR_PATH)
    print(f"✅ QR code généré : {QR_PATH}")
    print(f"📱 URL : {url}")

@app.route('/')
def index():
    """Page d'accueil - affiche le QR code"""
    # Générer le QR code si absent
    if not os.path.exists(QR_PATH):
        generate_qr()
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Système de Présence</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
            .container { max-width: 600px; margin: auto; }
            img { max-width: 100%; height: auto; border: 2px solid #333; }
            a { display: inline-block; margin: 10px; padding: 10px 20px; 
                background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 Système de Présence Géolocalisé</h1>
            <p>Scannez ce QR code avec votre téléphone pour enregistrer votre présence</p>
            <img src="/static/qr_math1.png" alt="QR Code">
            <div>
                <a href="/admin">👤 Interface Admin</a>
                <a href="/scan?cours=math1">📝 Scan Direct</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/scan')
def scan():
    """Page de scan pour les étudiants"""
    return render_template('scan.html')

@app.route('/admin')
def admin():
    """Page d'administration - affiche l'historique"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM presences ORDER BY id DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    return render_template('admin.html', rows=rows)

@app.route('/api/presence', methods=['POST'])
def record_presence():
    """API pour enregistrer une présence"""
    data = request.json
    
    if not data:
        return jsonify({'message': 'Données manquantes'}), 400
    
    name = data.get('name', '').strip()
    cours = data.get('cours', 'unknown')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not name:
        return jsonify({'message': 'Nom requis'}), 400
    
    if latitude is None or longitude is None:
        return jsonify({'message': 'Position GPS manquante'}), 400
    
    # Calculer la distance
    distance = haversine_distance(REF_LAT, REF_LON, latitude, longitude)
    
    # Déterminer le statut
    status = 'accepted' if distance <= MAX_DISTANCE_M else 'refused'
    
    # Enregistrer dans la base de données
    conn = get_db()
    c = conn.cursor()
    
    # Créer ou récupérer l'étudiant
    c.execute('INSERT OR IGNORE INTO students (name) VALUES (?)', (name,))
    c.execute('SELECT id FROM students WHERE name = ?', (name,))
    student = c.fetchone()
    student_id = student['id'] if student else None
    
    # Enregistrer la présence
    timestamp = datetime.utcnow().isoformat()
    c.execute('''INSERT INTO presences 
                 (student_id, name, cours, timestamp, latitude, longitude, distance, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (student_id, name, cours, timestamp, latitude, longitude, distance, status))
    
    conn.commit()
    conn.close()
    
    if status == 'accepted':
        return jsonify({
            'message': 'Présence enregistrée avec succès',
            'distance_m': distance,
            'status': status
        }), 200
    else:
        return jsonify({
            'message': f'Trop loin de la salle ({int(distance)}m > {MAX_DISTANCE_M}m)',
            'distance_m': distance,
            'status': status
        }), 403

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir les fichiers statiques"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Initialiser la base de données
    init_db()
    
    # Générer le QR code
    generate_qr()
    
    # Lancer l'application
    # IMPORTANT: Utiliser 0.0.0.0 pour Replit
    app.run(host='0.0.0.0', port=5000, debug=True)
