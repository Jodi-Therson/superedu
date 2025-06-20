import google.generativeai as genai

# --- Ganti dengan API key Anda ---
GOOGLE_API_KEY = ''
# ------------------------------------

# Konfigurasi API key
genai.configure(api_key=GOOGLE_API_KEY)
# --- System Instruction Final untuk SuperEdu ---

system_instruction = """
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
"""
# ----------------------------------------------------

# Membuat model dengan instruksi sistem
model = genai.GenerativeModel(
'gemini-2.0-flash',
system_instruction=system_instruction
)
# ====================================================================

# INILAH BAGIAN "MEMORI" NYA
# Kita memulai sesi chat yang akan menyimpan riwayat percakapan
chat = model.start_chat(history=[])
# ====================================================================


# Mengambil dan menampilkan pesan sapaan pertama dari bot
# Kita kirim pesan kosong untuk memicu sapaan awal
initial_response = chat.send_message("...")
print(f"SuperEdu: {initial_response.text}\n")


# Loop agar percakapan bisa berjalan terus menerus

while True:
    pertanyaan_user = input("Anda: ")

    if pertanyaan_user.lower() == 'selesai':
        print("SuperEdu: Tentu. Sampai jumpa lagi!")
        break
# ====================================================================

# PERUBAHAN KEDUA: MENGIRIM PESAN LEWAT SESI CHAT
  # Ini akan mengirim pertanyaan baru DAN seluruh riwayat sebelumnya
    response = chat.send_message(pertanyaan_user)
  # ====================================================================
    print(f"SuperEdu: {response.text}\n")