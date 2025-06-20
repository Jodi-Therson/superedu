from flask import Flask, render_template, request, Response, stream_with_context, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os, json
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import google.generativeai as genai

# Panggil load_dotenv() di awal untuk memuat variabel dari .env
load_dotenv()

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- KONFIGURASI GEMINI API ---
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Jika API Key tidak ditemukan, hentikan aplikasi atau berikan pesan error
    raise ValueError("GEMINI_API_KEY tidak ditemukan. Pastikan ada di file .env")

genai.configure(api_key=api_key)
# -----------------------------

# KUNCI RAHASIA: Diperlukan untuk Flask Sessions. Ganti dengan string acak Anda sendiri.
app.config['SECRET_KEY'] = 'kunci-rahasia-yang-sangat-sulit-ditebak-12345'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/superedu_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Letakkan ini di bagian atas app.py, setelah inisialisasi 'db'
ACHIEVEMENT_DEFINITIONS = {
    'Pemula': {
        'description': 'Berhasil bertanya sebanyak 3 kali.',
        'icon': '🌱',
        'condition_field': 'questions_asked_count', # Kolom di tabel user yang diperiksa
        'required_value': 3                      # Nilai yang harus dicapai
    },
    'Rasa Ingin Tahu': {
        'description': 'Berhasil bertanya sebanyak 10 kali.',
        'icon': '💡',
        'condition_field': 'questions_asked_count',
        'required_value': 10
    }
    # Anda bisa menambahkan achievement lain di sini
}

# --- MODEL DATABASE ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nis = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    questions_asked_count = db.Column(db.Integer, nullable=False, default=0)
    # Membuat relasi ke Achievement
    achievements = db.relationship('Achievement', backref='user', lazy=True)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_name = db.Column(db.String(100), nullable=False)
    unlocked_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
# ----------------------------------------------------

# Tambahkan fungsi ini di app.py
def check_and_award_achievements(user):
    """
    Memeriksa dan memberikan achievement baru kepada pengguna.
    Mengembalikan nama achievement yang baru didapat, atau None.
    """
    unlocked_names = {ach.achievement_name for ach in user.achievements}
    
    for name, details in ACHIEVEMENT_DEFINITIONS.items():
        if name not in unlocked_names:
            # Cek apakah syarat terpenuhi
            user_progress = getattr(user, details['condition_field'])
            if user_progress >= details['required_value']:
                # Syarat terpenuhi! Berikan achievement
                new_achievement = Achievement(user_id=user.id, achievement_name=name)
                db.session.add(new_achievement)
                return name # Kembalikan nama achievement yang baru didapat
    return None

# --- DECORATOR UNTUK MEWAJIBKAN LOGIN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: # Ganti 'user_nis' menjadi 'user_id'
            flash('Anda harus login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
# -------------------------------------------


# --- RUTE-RUTE BARU UNTUK OTENTIKASI ---

@app.route('/')
def home():
    # Jika sudah login, arahkan ke chat. Jika belum, arahkan ke login.
    if 'user_nis' in session:
        return redirect(url_for('chat_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nis = request.form['nis']
        password = request.form['password']
        
        # Query database untuk mencari user berdasarkan NIS
        user = User.query.filter_by(nis=nis).first()

        if user and check_password_hash(user.password_hash, password):
            # Login berhasil, simpan info pengguna di session
            session['logged_in'] = True
            session['user_id'] = user.id # Simpan ID, bukan NIS
            session['user_info'] = {
                'nama_lengkap': user.nama_lengkap,
                'username': user.username
            }
            flash('Login berhasil!', 'success')
            return redirect(url_for('chat_page'))
        else:
            flash('NIS atau Password salah. Silakan coba lagi.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Hapus semua data dari session
    session.clear()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    # Placeholder untuk logika ubah password
    # Anda perlu menambahkan validasi password lama, dll.
    new_password = request.form['new_password']
    # DUMMY_USERS[session['user_nis']]['password_hash'] = generate_password_hash(new_password)
    flash('Password berhasil diubah (simulasi).', 'success')
    return redirect(url_for('profile_page'))

# --- RUTE-RUTE LAMA YANG SEKARANG DILINDUNGI ---

@app.route('/chat')
@login_required
def chat_page():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile_page():
    # Ambil user dari database berdasarkan ID di session
    user_data = db.session.get(User, session['user_id']) 
    return render_template('profile.html', user=user_data)

@app.route('/achievements')
@login_required
def achievements_page():
    # Definisikan semua achievement yang mungkin ada di aplikasi
    ALL_ACHIEVEMENTS = {
        'Pencetus Ide': '🏆',
        'Ahli Aljabar': '➕',
        'Raja Kalkulus': '📈',
        'Misteri Geometri': '🔒',
        'Master Logika': '🔒'
    }

    # Ambil user dan achievement yang sudah dimiliki
    user = db.session.get(User, session['user_id'])
    unlocked_achievements_db = user.achievements # Ini adalah daftar objek Achievement
    
    # Buat set nama achievement yang sudah dimiliki untuk pencarian cepat
    unlocked_names = {ach.achievement_name for ach in unlocked_achievements_db}

    return render_template('achievements.html', 
                           all_achievements=ALL_ACHIEVEMENTS, 
                           unlocked_names=unlocked_names,
                           user=user)

@app.route('/history')
@login_required
def history_page():
    history_list = [
        {"subject": "Kalkulus", "question": "Jelaskan konsep limit tak hingga", "date": "15 Juni 2025"},
        {"subject": "Aljabar", "question": "bagaimana cara menyelesaikan soal limit fungsi aljabar?", "date": "14 Juni 2025"},
    ]
    return render_template('history.html', history_data=history_list)

@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')


# Rute untuk stream chat tidak perlu login_required karena diakses oleh JavaScript
# Keamanannya adalah halaman yang memuat JavaScript itu sendiri sudah dilindungi.
@app.route('/stream_chat', methods=['POST'])
@login_required
def stream_chat():
    # Ambil seluruh history dari request, bukan lagi satu pesan
    incoming_history = request.json.get('history', [])
    if not incoming_history:
        return Response("Riwayat percakapan kosong.", status=400)

    user = db.session.get(User, session['user_id'])
    
    # Logika achievement tidak perlu diubah
    user.questions_asked_count += 1
    newly_unlocked_achievement_name = check_and_award_achievements(user)
    db.session.commit()

    def generate_responses():
        try:
            # Tetap definisikan system instruction
            system_instruction_text = """
            Kamu adalah "SuperEdu", seorang asisten virtual dan tutor matematika yang sabar, cerdas, dan suportif. Tujuan utamamu bukan memberikan jawaban langsung, melainkan memandu pengguna untuk menemukan jawaban sendiri.
            **Aturan Perilaku dan Alur Kerja:**
            1. **Menerima Soal:** Ketika pengguna memberikan sebuah soal atau meminta bantuan untuk mencari rumus, tugasmu adalah menjelaskan METODE atau LANGKAH-LANGKAH untuk menyelesaikannya.
            2. **JANGAN Berikan Jawaban Akhir:** Setelah menjelaskan metodenya, JANGAN PERNAH memberikan jawaban numerik atau rumus jadinya. Sebaliknya, akhiri penjelasanmu dengan sebuah ajakan agar pengguna mencoba menjawab.
            3. **Menunggu dan Mengevaluasi Jawaban:** Setelah pengguna mengirimkan jawabannya, evaluasi jawaban tersebut. Jika benar, beri pujian. Jika salah, beri tahu dan lacak jumlah kesalahan.
            4. **Logika Tiga Kali Kesempatan dan Bantuan:**
            * **Kesalahan Pertama & Kedua:** Beri tahu pengguna bahwa jawabannya salah dan dorong mereka untuk mencoba lagi.
            * **Kesalahan Ketiga:** Berikan petunjuk yang substansial yang hampir menjawab sebagian dari persoalan.
            * **Setelah Kesalahan Ketiga Gagal:** Berikan jawaban yang benar beserta penjelasan lengkapnya, lalu tawarkan soal serupa untuk menguji pemahaman.
            5. **Batasan Topik:** Fokus hanya pada topik matematika. Jika ditanya di luar topik, tolak dengan sopan.
            6. **Catat jawaban yang diberikan, analisa apakah setiap jawaban memberikan perkembangan ke arah jawaban yang benar. Jangan biarkan pengguna sengaja menjawab salah hanya untuk mendapatkan jawaban benarnya.
            """
            model = genai.GenerativeModel(
                'gemini-2.0-flash',
                system_instruction=system_instruction_text
            )

            # << BAGIAN UTAMA YANG BERUBAH >>
            # 1. Format ulang history dari frontend ke format yang dimengerti Gemini API
            gemini_history = []
            for message in incoming_history:
                gemini_history.append({
                    "role": message["role"],
                    "parts": [{"text": message["content"]}]
                })
            
            # 2. Kirim seluruh history ke Gemini, bukan hanya satu pesan
            response_stream = model.generate_content(gemini_history, stream=True)

            # Kumpulkan respons dari AI untuk disimpan ke history di frontend
            full_ai_response = ""
            for chunk in response_stream:
                full_ai_response += chunk.text
                yield f"data: {json.dumps({'type': 'message', 'content': chunk.text})}\n\n"
            
            # (Optional tapi direkomendasikan) Anda bisa menyimpan `full_ai_response` ini ke database
            # untuk riwayat belajar di halaman History.

            # Logika pengiriman achievement tidak berubah
            if newly_unlocked_achievement_name:
                details = ACHIEVEMENT_DEFINITIONS[newly_unlocked_achievement_name]
                achievement_data = {
                    "name": newly_unlocked_achievement_name,
                    "icon": details['icon'],
                    "description": details['description']
                }
                yield f"event: achievement_unlocked\ndata: {json.dumps(achievement_data)}\n\n"

        except Exception as e:
            error_message = f"Terjadi kesalahan saat menghubungi AI: {e}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_message})}\n\n"

    return Response(stream_with_context(generate_responses()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5001)