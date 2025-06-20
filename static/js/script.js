document.addEventListener('DOMContentLoaded', () => {

    // === LOGIKA GLOBAL UNTUK SEMUA HALAMAN (DARI BASE.HTML) ===
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mainContent = document.getElementById('main-content');

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', (event) => {
            event.stopPropagation(); // Mencegah event klik menyebar ke dokumen
            sidebar.classList.toggle('open');
        });
    }

    if (mainContent) {
        // Menutup sidebar jika pengguna mengklik di area konten utama
        mainContent.addEventListener('click', () => {
            if (sidebar && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        });
    }

    // === LOGIKA KHUSUS UNTUK HALAMAN LOGIN (`login.html`) ===
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
        const passwordInput = document.getElementById('password');
        const togglePassword = document.getElementById('toggle-password');

        if (togglePassword && passwordInput) {
            const eyeIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-eye-fill" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/></svg>`;
            const eyeSlashIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-eye-slash-fill" viewBox="0 0 16 16"><path d="m10.79 12.912-1.614-1.615a3.5 3.5 0 0 1-4.474-4.474l-2.06-2.06C.938 6.278 0 8 0 8s3 5.5 8 5.5a7.029 7.029 0 0 0 2.79-.588zM5.21 3.088A7.028 7.028 0 0 1 8 2.5c5 0 8 5.5 8 5.5s-.939 1.721-2.641 3.238l-2.062-2.062a3.5 3.5 0 0 0-4.474-4.474L5.21 3.089z"/><path d="M5.525 7.646a2.5 2.5 0 0 0 2.829 2.829l-2.83-2.829zm4.95.708-2.829-2.83a2.5 2.5 0 0 1 2.829 2.829zm3.171 6-12-12 .708-.708 12 12-.708.708z"/></svg>`;

            togglePassword.addEventListener('click', function () {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
                this.innerHTML = type === 'password' ? eyeIcon : eyeSlashIcon;
            });
        }
    }


    // === LOGIKA KHUSUS UNTUK HALAMAN CHAT (`index.html`) ===
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        const messageInput = document.getElementById('message-input');
        const messageList = document.getElementById('message-list');
        let chatHistory = []; // 1. Variabel untuk menyimpan riwayat chat

        // 2. Fungsi displayMessage kini punya DUA tugas: menampilkan di layar DAN menyimpan ke history
        function displayMessage(sender, text) {
            // Bagian untuk menampilkan di layar (tidak berubah)
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', sender);
            const bubbleDiv = document.createElement('div');
            bubbleDiv.classList.add('bubble');
            bubbleDiv.textContent = text;
            messageDiv.appendChild(bubbleDiv);
            messageList.appendChild(messageDiv);
            messageList.scrollTop = messageList.scrollHeight;

            // Tugas baru: Menyimpan ke array chatHistory
            // Kita ubah 'assistant' menjadi 'model' agar sesuai format API Gemini
            const role = (sender === 'assistant') ? 'model' : 'user';
            chatHistory.push({ role: role, content: text });

            return bubbleDiv; // Kembalikan bubble agar bisa di-update oleh stream
        }

        function showTypingIndicator() {
            if (document.getElementById('typing-indicator')) return; // Jangan tambah jika sudah ada
            const typingDiv = document.createElement('div');
            typingDiv.classList.add('message', 'assistant', 'typing');
            typingDiv.id = 'typing-indicator';
            const bubbleDiv = document.createElement('div');
            bubbleDiv.classList.add('bubble');
            bubbleDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            typingDiv.appendChild(bubbleDiv);
            messageList.appendChild(typingDiv);
            messageList.scrollTop = messageList.scrollHeight;
        }

        function hideTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) {
                indicator.remove();
            }
        }

        // 3. Fungsi sendMessageToBackend sekarang mengirim seluruh history
        async function sendMessageToBackend() {
            showTypingIndicator();
            let assistantBubble; // Pindahkan deklarasi ke sini

            try {
                const response = await fetch('/stream_chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ history: chatHistory }) // Mengirim seluruh history
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullAiResponse = ""; // Variabel untuk mengumpulkan respons AI

                // Loop untuk membaca stream dari server
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        // Aliran selesai, simpan respons lengkap AI ke history
                        if(fullAiResponse) {
                            // Hapus bubble sementara dan ganti dengan bubble permanen berisi respons lengkap
                            if(assistantBubble) assistantBubble.parentElement.remove();
                            displayMessage('assistant', fullAiResponse);
                        }
                        break;
                    }

                    hideTypingIndicator();
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data:')) {
                            const data = JSON.parse(line.substring(5));

                            if (data.type === 'error') {
                                console.error("Server Error:", data.content);
                                if (!assistantBubble) assistantBubble = displayMessage('assistant', '');
                                assistantBubble.textContent = `Error: ${data.content}`;
                                assistantBubble.style.color = 'red';
                                chatHistory.push({ role: 'model', content: `Error: ${data.content}` }); // Simpan error ke history
                                return; // Hentikan jika error
                            }

                            if (data.type === 'message') {
                                if (!assistantBubble) {
                                     // Buat bubble sementara untuk diisi oleh stream
                                    const tempMessageDiv = document.createElement('div');
                                    tempMessageDiv.classList.add('message', 'assistant');
                                    assistantBubble = document.createElement('div');
                                    assistantBubble.classList.add('bubble');
                                    tempMessageDiv.appendChild(assistantBubble);
                                    messageList.appendChild(tempMessageDiv);
                                }
                                assistantBubble.textContent += data.content;
                                fullAiResponse += data.content; // Kumpulkan respons
                                messageList.scrollTop = messageList.scrollHeight;
                            }
                        } else if (line.startsWith('event: achievement_unlocked')) {
                            const nextLine = lines[lines.indexOf(line) + 1];
                            if (nextLine && nextLine.startsWith('data:')) {
                                const achievement = JSON.parse(nextLine.substring(5));
                                alert(`🏆 Achievement Unlocked! 🏆\n\n${achievement.name}\n${achievement.description}`);
                            }
                        }
                    }
                }

            } catch (error) {
                console.error('Error sending message:', error);
                hideTypingIndicator();
                displayMessage('assistant', 'Maaf, terjadi kesalahan saat mengirim pesan.');
            }
        }
        
        // 4. Event listener form diubah untuk mengikuti alur baru
        chatForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const userMessage = messageInput.value.trim();
            if (userMessage) {
                // Tampilkan pesan user (sekaligus menyimpannya ke history)
                displayMessage('user', userMessage);
                // Kirim history ke backend untuk mendapatkan respons AI
                sendMessageToBackend();
                messageInput.value = '';
            }
        });

        // Menampilkan dan menyimpan pesan sapaan awal
        if (messageList.children.length === 0) {
            displayMessage('assistant', 'Halo! Saya SuperEdu, siap membantumu belajar matematika. Ada soal apa hari ini?');
        }
    }

    // === LOGIKA KHUSUS UNTUK HALAMAN PENGATURAN (`settings.html`) ===
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const selectedTheme = document.querySelector('input[name="theme"]:checked').value;
            const selectedChar = document.querySelector('input[name="character"]:checked').value;
            alert(`Pengaturan disimpan!\nTema: ${selectedTheme}\nKarakter: ${selectedChar}\n\n(Fungsionalitas penyimpanan belum diimplementasikan)`);
        });
    }
});