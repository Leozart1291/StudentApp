// Только видео жестов — список слов берётся из загруженных видео (gestureVideosList)
let gestureWords = [];
let currentWordIndex = 0;

// Функция создания частиц
function createParticles(element) {
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    for (let i = 0; i < 12; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';

        const angle = (Math.PI * 2 * i) / 12;
        const distance = 100;
        const tx = Math.cos(angle) * distance;
        const ty = Math.sin(angle) * distance;

        particle.style.left = centerX + 'px';
        particle.style.top = centerY + 'px';
        particle.style.setProperty('--tx', tx + 'px');
        particle.style.setProperty('--ty', ty + 'px');
        particle.style.animation = 'particleFly 0.8s ease-out forwards';

        document.body.appendChild(particle);

        setTimeout(() => {
            particle.remove();
        }, 800);
    }
}

// Показать слово и воспроизвести только видео жеста (без эмодзи)
function showWordAndGesture() {
    const wordDisplay = document.getElementById('word-display');
    const gestureContent = document.getElementById('gestureContent');
    const gestureDisplay = document.getElementById('gesture-display');
    const gestureVideo = document.getElementById('gestureVideo');

    if (gestureWords.length === 0) return;

    const currentWord = gestureWords[currentWordIndex];
    const video = findGestureVideo(currentWord);

    gestureDisplay.textContent = '';
    if (gestureContent) gestureContent.style.display = 'flex';
    if (gestureVideo) gestureVideo.style.display = 'none';

    wordDisplay.classList.remove('enter', 'exit');
    wordDisplay.textContent = currentWord;
    wordDisplay.classList.add('enter');

    if (video) {
        setTimeout(function () {
            if (gestureContent) gestureContent.style.display = 'none';
            if (gestureVideo) gestureVideo.style.display = 'block';
            playGestureVideo(video, false);
        }, 1500);
    }

    currentWordIndex = (currentWordIndex + 1) % gestureWords.length;
}

// Функция обновления текста урока
function updateLessonText(text) {
    const lessonText = document.getElementById('lesson-text');
    const newParagraph = document.createElement('p');
    newParagraph.textContent = text;
    lessonText.appendChild(newParagraph);

    // Автоматическая прокрутка вниз
    lessonText.scrollTop = lessonText.scrollHeight;
}

// Функционал чата
function initializeChat() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');

    if (!messageInput || !sendButton || !chatMessages) {
        return; // Элементы не найдены
    }

    let lastMessageId = 0;
    let isSending = false;

    // Проверка наличия access_code
    if (typeof lessonAccessCode === 'undefined' || !lessonAccessCode) {
        console.warn('Access code не найден, чат не будет работать');
        messageInput.disabled = true;
        sendButton.disabled = true;
        return;
    }

    // Функция отправки сообщения
    async function sendMessage() {
        const messageText = messageInput.value.trim();
        if (messageText === '' || isSending) return;

        isSending = true;
        sendButton.disabled = true;

        try {
            const response = await fetch(`/api/lesson/${lessonAccessCode}/chat/send`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({message: messageText})
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Сообщение успешно отправлено
                messageInput.value = '';
                // Сообщение будет добавлено при следующей загрузке
                loadChatMessages();
            } else {
                alert('Ошибка отправки сообщения: ' + (data.error || 'Неизвестная ошибка'));
            }
        } catch (error) {
            console.error('Ошибка отправки сообщения:', error);
            alert('Не удалось отправить сообщение. Проверьте подключение к интернету.');
        } finally {
            isSending = false;
            sendButton.disabled = false;
        }
    }

    // Функция отображения сообщения
    function displayMessage(message) {
        // Проверить, не добавлено ли уже это сообщение
        const existingMessage = chatMessages.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMessage) {
            return; // Сообщение уже отображено
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.setAttribute('data-message-id', message.id);

        // Определить, является ли сообщение отправленным текущим пользователем
        const isCurrentUser = message.user_id === (window.currentUserId || null);

        if (isCurrentUser) {
            messageDiv.classList.add('sent');
        } else {
            messageDiv.classList.add('received');
        }

        // Добавить информацию об отправителе
        const senderInfo = document.createElement('div');
        senderInfo.className = 'message-sender';

        const roleLabel = message.role === 'teacher' ? 'Учитель' : 'Ученик';
        senderInfo.textContent = roleLabel + ': ' + message.username;

        // Текст сообщения
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = message.message;

        // Время отправки
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        if (message.timestamp) {
            const date = new Date(message.timestamp);
            messageTime.textContent = date.toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
        }

        messageDiv.appendChild(senderInfo);
        messageDiv.appendChild(messageText);
        messageDiv.appendChild(messageTime);

        chatMessages.appendChild(messageDiv);

        // Прокрутить вниз
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Обновить lastMessageId
        if (message.id > lastMessageId) {
            lastMessageId = message.id;
        }
    }

    // Функция загрузки сообщений
    async function loadChatMessages() {
        try {
            const response = await fetch(`/api/lesson/${lessonAccessCode}/chat/messages?last_id=${lastMessageId}`);
            const data = await response.json();

            if (response.ok && data.success && data.messages) {
                // Отобразить новые сообщения
                data.messages.forEach(message => {
                    displayMessage(message);
                });
            }
        } catch (error) {
            console.error('Ошибка загрузки сообщений:', error);
        }
    }

    // Обработчики событий
    sendButton.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Загрузить существующие сообщения при загрузке страницы
    loadChatMessages();

    // Автоматическое обновление сообщений каждые 2 секунды
    setInterval(loadChatMessages, 2000);

    // Экспортировать функцию для внешнего использования
    window.loadChatMessages = loadChatMessages;
}

// Управление камерой учителя (и отображение кадра у учеников)
let localStream = null;
let teacherFrameCaptureInterval = null;

function initializeCamera() {
    const startCameraBtn = document.getElementById('startCameraBtn');
    const stopCameraBtn = document.getElementById('stopCameraBtn');
    const cameraPlaceholder = document.getElementById('cameraPlaceholder');
    const teacherVideo = document.getElementById('teacherVideo');
    const teacherFrameImage = document.getElementById('teacherFrameImage');
    const cameraControls = document.getElementById('cameraControls');
    const isTeacher = (typeof currentUserRole !== 'undefined' && currentUserRole === 'teacher');

    // Ученики: показываем кадр камеры учителя с сервера (опрос)
    if (!isTeacher && typeof lessonAccessCode !== 'undefined' && lessonAccessCode && teacherFrameImage) {
        teacherFrameImage.style.display = 'none';
        cameraPlaceholder.style.display = 'flex';
        if (cameraPlaceholder.querySelector('p')) cameraPlaceholder.querySelector('p').textContent = 'Камера учителя';
        const startBtn = cameraPlaceholder.querySelector('#startCameraBtn');
        if (startBtn) startBtn.style.display = 'none';

        function pollTeacherFrame() {
            fetch(`/api/lesson/${lessonAccessCode}/teacher-frame`)
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.frame) {
                        teacherFrameImage.src = 'data:image/jpeg;base64,' + data.frame;
                        teacherFrameImage.style.display = 'block';
                        cameraPlaceholder.style.display = 'none';
                    }
                })
                .catch(() => {
                });
        }

        pollTeacherFrame();
        setInterval(pollTeacherFrame, 200);
        return;
    }

    // Проверка поддержки getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        // Попытка использовать устаревший API
        navigator.getUserMedia = navigator.getUserMedia ||
            navigator.webkitGetUserMedia ||
            navigator.mozGetUserMedia ||
            navigator.msGetUserMedia;

        if (!navigator.getUserMedia) {
            console.error('Ваш браузер не поддерживает доступ к камере');
            if (startCameraBtn) {
                startCameraBtn.textContent = 'Камера не поддерживается';
                startCameraBtn.disabled = true;
            }
            return;
        }
    }

    // Функция запуска камеры
    async function startCamera() {
        try {
            const constraints = {
                video: {
                    width: {ideal: 1280},
                    height: {ideal: 720},
                    facingMode: "user"
                },
                audio: true
            };

            let stream;
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                stream = await navigator.mediaDevices.getUserMedia(constraints);
            } else {
                stream = await new Promise((resolve, reject) => {
                    navigator.getUserMedia(constraints, resolve, reject);
                });
            }

            localStream = stream;

            // Видео
            if (teacherVideo) {
                teacherVideo.srcObject = stream;
                teacherVideo.style.display = "block";
            }

            // Убираем кадр (для учеников)
            const frameImg = document.getElementById("teacherFrameImage");
            if (frameImg) frameImg.style.display = "none";

            // UI: прячем placeholder, показываем кнопки
            if (cameraPlaceholder) cameraPlaceholder.style.display = "none";
            if (cameraControls) cameraControls.style.display = "flex"; // ✅ важно: flex

            // На всякий: если CSS случайно давал display:none — убираем класс/атрибут
            if (cameraControls) cameraControls.removeAttribute("hidden");

            const camBox = document.querySelector('.main-video-container');
            if (camBox) camBox.classList.add('camera-on');

            // Отправка кадра на сервер
            if (typeof lessonAccessCode !== "undefined" && lessonAccessCode) {
                if (teacherFrameCaptureInterval) clearInterval(teacherFrameCaptureInterval);

                teacherFrameCaptureInterval = setInterval(function captureAndSendFrame() {
                    if (!teacherVideo || !teacherVideo.srcObject || teacherVideo.readyState < 2) return;

                    try {
                        const canvas = document.createElement("canvas");
                        canvas.width = teacherVideo.videoWidth || 640;
                        canvas.height = teacherVideo.videoHeight || 360;

                        const ctx = canvas.getContext("2d");
                        ctx.drawImage(teacherVideo, 0, 0);

                        const dataUrl = canvas.toDataURL("image/jpeg", 0.5);
                        const base64 = dataUrl.replace(/^data:image\/jpeg;base64,/, "");

                        fetch(`/api/lesson/${lessonAccessCode}/teacher-frame`, {
                            method: "POST",
                            headers: {"Content-Type": "application/json"},
                            body: JSON.stringify({frame: base64})
                        }).catch(() => {
                        });
                    } catch (e) {
                    }
                }, 150);
            }

            console.log("Камера успешно включена");
        } catch (error) {
            console.error("Ошибка доступа к камере:", error);
            alert("Не удалось получить доступ к камере. Пожалуйста, проверьте разрешения в настройках браузера.");

            if (startCameraBtn) {
                startCameraBtn.textContent = "Ошибка подключения";
                startCameraBtn.disabled = true;
                setTimeout(() => {
                    startCameraBtn.textContent = "Включить камеру";
                    startCameraBtn.disabled = false;
                }, 3000);
            }
        }
    }

    // Функция остановки камеры
    function stopCamera() {
        if (teacherFrameCaptureInterval) {
            clearInterval(teacherFrameCaptureInterval);
            teacherFrameCaptureInterval = null;
        }
        // Остановить распознавание речи, если оно активно
        if (window.stopSpeechRecognition) {
            window.stopSpeechRecognition();
        }

        if (localStream) {
            // Остановить все треки потока
            localStream.getTracks().forEach(track => {
                track.stop();
            });
            localStream = null;
        }

        // Скрыть видео
        if (teacherVideo) {
            teacherVideo.srcObject = null;
            teacherVideo.style.display = 'none';
        }

        // Показать placeholder и скрыть controls
        if (cameraPlaceholder) {
            cameraPlaceholder.style.display = 'flex';
        }
        if (cameraControls) {
            cameraControls.style.display = 'none';
        }

        console.log('Камера выключена');
        const camBox = document.querySelector('.main-video-container');
        if (camBox) camBox.classList.remove('camera-on');
    }

    // Обработчики событий
    if (startCameraBtn) {
        startCameraBtn.addEventListener('click', startCamera);
    }

    if (stopCameraBtn) {
        stopCameraBtn.addEventListener('click', stopCamera);
    }

    const camBox = document.querySelector('.main-video-container');
    if (camBox) camBox.classList.remove('camera-on');

    // Остановить камеру при закрытии страницы
    window.addEventListener('beforeunload', stopCamera);
}

// Управление видео жестов
let gestureVideosList = [];
let currentGestureVideo = null;

// Загрузка списка видео жестов
async function loadGestureVideos() {
    try {
        const response = await fetch('/api/gesture-videos/list');
        const data = await response.json();
        if (data.success && data.videos) {
            gestureVideosList = data.videos;
            gestureWords = data.videos.map(function (v) {
                return v.text;
            });
            console.log('Загружено видео жестов:', gestureVideosList.length);
        }
    } catch (error) {
        console.error('Ошибка загрузки списка видео:', error);
    }
}

// Оригинальный текст параграфа урока (для подсветки текущего слова синим)
var originalLessonParagraphText = '';

function escapeHtml(s) {
    if (!s) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Подсветить в параграфе урока текущее слово синим (пока идёт видео жеста)
function highlightWordInLessonParagraph(phrase) {
    var p = document.getElementById('lesson-description-p');
    if (!p || !originalLessonParagraphText) return;
    var text = originalLessonParagraphText;
    var word = (phrase || '').trim();
    if (!word) {
        p.textContent = text;
        return;
    }
    var esc = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    var re = new RegExp('(\\b' + esc + '\\b)', 'i');
    var match = text.match(re);
    if (!match) {
        p.textContent = text;
        return;
    }
    var idx = text.indexOf(match[1]);
    var before = text.slice(0, idx);
    var found = text.slice(idx, idx + match[1].length);
    var after = text.slice(idx + match[1].length);
    p.innerHTML = escapeHtml(before) + '<span class="current-word">' + escapeHtml(found) + '</span>' + escapeHtml(after);
}

// Единая очередь воспроизведения: по словам из текста искать видео в video/ и показывать в блоке жестов
function enqueueVideosFromText(text) {
    if (!text || !String(text).trim()) return;
    if (gestureVideosList.length === 0) return;
    var words = String(text).split(/[\s.,!?;:()\[\]{}–—]+/).filter(function (w) {
        return w.length > 0;
    });
    words.forEach(function (word) {
        var clean = word.replace(/[^\w\u0400-\u04FF]/gi, '').trim();
        if (clean.length < 1) return;
        var video = findGestureVideo(clean);
        simplifiedTextPlaybackQueue.push({phrase: clean, video: video, index: simplifiedTextPlaybackQueue.length});
    });
    if (simplifiedTextPlaybackQueue.length > 0 && !isPlayingSimplifiedText) {
        playNextSimplifiedGesture();
    }
}

// Функция нормализации текста для сравнения
function normalizeText(text) {
    return text.toLowerCase()
        .replace(/[.,!?;:]/g, '') // Убрать знаки препинания
        .replace(/\s+/g, ' ') // Множественные пробелы в один
        .trim();
}

// Функция поиска видео по тексту
function findGestureVideo(text) {
    if (!text || gestureVideosList.length === 0) return null;

    const normalizedText = normalizeText(text);

    // Точное совпадение
    for (const video of gestureVideosList) {
        const normalizedVideoText = normalizeText(video.text);
        if (normalizedText === normalizedVideoText) {
            return video;
        }
    }

    // Частичное совпадение (текст содержит название видео)
    for (const video of gestureVideosList) {
        const normalizedVideoText = normalizeText(video.text);
        if (normalizedText.includes(normalizedVideoText) || normalizedVideoText.includes(normalizedText)) {
            return video;
        }
    }

    // Поиск по словам (если распознанный текст содержит ключевые слова из названия видео)
    const textWords = normalizedText.split(' ').filter(w => w.length > 2);
    for (const video of gestureVideosList) {
        const videoWords = normalizeText(video.text).split(' ').filter(w => w.length > 2);
        // Проверить, есть ли совпадение хотя бы 2 слов
        const matchingWords = textWords.filter(word => videoWords.includes(word));
        if (matchingWords.length >= 2 || (videoWords.length <= 3 && matchingWords.length >= 1)) {
            return video;
        }
    }

    return null;
}

// Функция воспроизведения видео жеста
function playGestureVideo(video, isFromServer = false) {
    const gestureVideo = document.getElementById('gestureVideo');
    const gestureContent = document.getElementById('gestureContent');

    if (!gestureVideo || !video) return;

    // Если уже воспроизводится то же видео, не перезапускать
    if (currentGestureVideo && currentGestureVideo.url === video.url && !gestureVideo.paused) {
        return;
    }

    currentGestureVideo = video;

    // Скрыть старую анимацию
    if (gestureContent) {
        gestureContent.style.display = 'none';
    }

    // Показать видеоплеер
    gestureVideo.style.display = 'block';
    gestureVideo.src = video.url;

    // Воспроизвести видео
    gestureVideo.play().catch(error => {
        console.error('Ошибка воспроизведения видео:', error);
    });

    // Когда видео закончится, показать старую анимацию
    gestureVideo.onended = function () {
        gestureVideo.style.display = 'none';
        if (gestureContent) {
            gestureContent.style.display = 'flex';
        }
        currentGestureVideo = null;
    };

    console.log('Воспроизведение видео жеста:', video.text, isFromServer ? '(от сервера)' : '(локально)');

    // Если это не от сервера и есть access_code, отправить информацию на сервер для синхронизации
    if (!isFromServer && typeof lessonAccessCode !== 'undefined' && lessonAccessCode) {
        sendGestureVideoToServer(video);
    }
}

// Функция отправки видео на сервер (для учителя)
async function sendGestureVideoToServer(video) {
    if (typeof lessonAccessCode === 'undefined' || !lessonAccessCode) return;

    try {
        await fetch(`/api/lesson/${lessonAccessCode}/gesture-video/set`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: video.url,
                text: video.text
            })
        });
    } catch (error) {
        console.error('Ошибка отправки видео на сервер:', error);
    }
}

// Последний запрошенный текст для объяснения (чтобы не дублировать запросы)
let lastExplainedText = '';
let lastExplainedTime = 0;
const EXPLAIN_DEBOUNCE_MS = 8000;

// Запросить у ИИ (Gemini) объяснение текста для глухих, когда нет видео жеста
async function fetchAIExplanationForSignLanguage(text) {
    if (!text || text.length < 3) return;
    const normalized = normalizeText(text);
    if (normalized === normalizeText(lastExplainedText) && (Date.now() - lastExplainedTime) < EXPLAIN_DEBOUNCE_MS) {
        return;
    }
    lastExplainedText = text;
    lastExplainedTime = Date.now();

    const container = document.getElementById('ai-explanation-container');
    const originalEl = document.getElementById('aiExplanationOriginal');
    const textEl = document.getElementById('aiExplanationText');
    if (!container || !textEl) return;

    textEl.textContent = 'Загрузка объяснения...';
    if (originalEl) originalEl.textContent = '';
    container.style.display = 'block';
    textEl.scrollIntoView({behavior: 'smooth', block: 'nearest'});

    try {
        const response = await fetch('/api/explain-for-sign-language', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: text})
        });
        const data = await response.json();

        if (response.ok && data.success && data.explanation) {
            if (originalEl) {
                originalEl.textContent = 'Услышано: «' + (data.original || text) + '»';
                originalEl.style.display = 'block';
            }
            textEl.textContent = data.explanation;
            textEl.style.whiteSpace = 'pre-wrap';
        } else {
            textEl.textContent = 'Не удалось получить объяснение. Попробуйте ещё раз.';
            if (originalEl) originalEl.style.display = 'none';
        }
    } catch (error) {
        console.error('Ошибка запроса объяснения:', error);
        textEl.textContent = 'Ошибка соединения. Проверьте интернет.';
        if (originalEl) originalEl.style.display = 'none';
    }
}

// Функция проверки нового видео от сервера (для учеников и учителя)
let lastVideoTimestamp = null;

async function checkForNewGestureVideo() {
    if (typeof lessonAccessCode === 'undefined' || !lessonAccessCode) return;

    try {
        const url = `/api/lesson/${lessonAccessCode}/gesture-video/get${lastVideoTimestamp ? '?last_timestamp=' + lastVideoTimestamp : ''}`;
        const response = await fetch(url);
        const data = await response.json();

        if (response.ok && data.success && data.video) {
            // Получено новое видео
            const video = {
                url: data.video.url,
                text: data.video.text
            };

            // Воспроизвести видео (помечаем как от сервера, чтобы не отправлять обратно)
            playGestureVideo(video, true);

            // Обновить timestamp
            lastVideoTimestamp = data.video.timestamp;
        }
    } catch (error) {
        console.error('Ошибка проверки видео от сервера:', error);
    }
}

// Инициализация распознавания речи
function initializeSpeechRecognition() {
    const startSpeechBtn = document.getElementById('startSpeechBtn');
    const startSpeechBtnSubtitle = document.getElementById('startSpeechBtnSubtitle');
    const subtitlesContainer = document.getElementById('subtitles-container');
    const subtitlesText = document.getElementById('subtitles-text');

    // Проверка поддержки Speech Recognition API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('Ваш браузер не поддерживает распознавание речи');
        if (startSpeechBtn) {
            startSpeechBtn.textContent = 'Распознавание речи не поддерживается';
            startSpeechBtn.disabled = true;
        }
        if (startSpeechBtnSubtitle) {
            startSpeechBtnSubtitle.textContent = 'Не поддерживается';
            startSpeechBtnSubtitle.disabled = true;
        }
        return;
    }
    // Ученикам кнопку «Распознавание» в субтитрах не показывать (субтитры приходят с сервера)
    if (typeof currentUserRole !== 'undefined' && currentUserRole === 'student' && startSpeechBtnSubtitle) {
        startSpeechBtnSubtitle.style.display = 'none';
    }

    let recognition = null;
    let isRecognizing = false;
    let finalTranscript = '';
    const MAX_SENTENCES = 10; // Хранить последние 10 предложений целиком
    let lastProcessedText = ''; // Для отслеживания уже обработанных фраз

    function trimToLastSentences(text, maxSentences) {
        if (!text || maxSentences <= 0) return text;
        const parts = text.split(/([.!?]\s+)/);
        const sentences = [];
        let buf = '';
        for (let i = 0; i < parts.length; i++) {
            buf += parts[i];
            if (/[.!?]\s*$/.test(parts[i])) {
                sentences.push(buf.trim());
                buf = '';
            }
        }
        if (buf.trim()) sentences.push(buf.trim());
        if (sentences.length <= maxSentences) return text;
        return sentences.slice(-maxSentences).join(' ');
    }

    // Функция запуска распознавания речи
    function startSpeechRecognition() {
        if (isRecognizing) {
            stopSpeechRecognition();
            return;
        }

        try {
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;
            recognition.lang = 'ru-RU';

            recognition.onstart = function () {
                isRecognizing = true;
                if (startSpeechBtn) {
                    startSpeechBtn.textContent = 'Остановить распознавание';
                    startSpeechBtn.classList.add('active');
                }
                if (startSpeechBtnSubtitle) {
                    startSpeechBtnSubtitle.textContent = 'Остановить распознавание';
                    startSpeechBtnSubtitle.classList.add('active');
                }
                if (subtitlesContainer) subtitlesContainer.classList.add('visible');
                if (subtitlesText) subtitlesText.textContent = 'Говорите…';
                console.log('Распознавание речи начато');
            };

            recognition.onresult = function (event) {
                if (!event.results || event.results.length === 0) return;
                var interimTranscript = '';
                var newFinalText = '';
                for (var i = event.resultIndex; i < event.results.length; i++) {
                    var result = event.results[i];
                    var transcript = '';
                    try {
                        transcript = (result[0] && result[0].transcript) ? result[0].transcript : '';
                    } catch (e) {
                        continue;
                    }
                    if (result.isFinal) {
                        finalTranscript += transcript + ' ';
                        newFinalText += transcript + ' ';
                    } else {
                        interimTranscript += transcript;
                    }
                }
                finalTranscript = trimToLastSentences(finalTranscript.trim() + ' ', MAX_SENTENCES).trim();
                var displayText = (finalTranscript + ' ' + interimTranscript).trim();
                if (subtitlesText) {
                    subtitlesText.textContent = displayText || 'Говорите…';
                }
                if (subtitlesContainer) {
                    subtitlesContainer.classList.add('visible');
                }
                // Отправить субтитры на сервер для учеников (учитель)
                if (typeof lessonAccessCode !== 'undefined' && lessonAccessCode && (typeof currentUserRole !== 'undefined' && currentUserRole === 'teacher')) {
                    fetch(`/api/lesson/${lessonAccessCode}/teacher-subtitle`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: displayText})
                    }).catch(() => {
                    });
                }

                // По словам из субтитров искать видео в video/ и ставить в очередь в блок жестов
                if (newFinalText.trim()) {
                    var normalizedNewText = normalizeText(newFinalText);
                    if (normalizedNewText !== normalizeText(lastProcessedText)) {
                        lastProcessedText = newFinalText;
                        enqueueVideosFromText(newFinalText.trim());
                        var words = normalizedNewText.split(' ').filter(function (w) {
                            return w.length > 0;
                        });
                        if (words.length >= 2 && typeof fetchAIExplanationForSignLanguage === 'function') {
                            fetchAIExplanationForSignLanguage(newFinalText.trim());
                        }
                    }
                }
            };

            recognition.onerror = function (event) {
                console.error('Ошибка распознавания речи:', event.error);
                if (event.error === 'no-speech') return;
                if (event.error === 'not-allowed') {
                    if (subtitlesText) subtitlesText.textContent = 'Микрофон құқығы берілмеді. Браузер параметрлерін тексеріңіз.';
                    alert('Доступ к микрофону запрещен. Разрешите микрофон в настройках браузера (иконка замка в адресной строке).');
                    stopSpeechRecognition();
                    return;
                }
                if (event.error === 'network') {
                    if (subtitlesText) subtitlesText.textContent = 'Желі қатесі. Chrome браузерінде HTTPS қажет.';
                }
            };

            recognition.onend = function () {
                if (!isRecognizing) return;
                try {
                    recognition.start();
                } catch (e) {
                    console.error('Ошибка перезапуска распознавания:', e);
                    stopSpeechRecognition();
                }
            };

            recognition.start();
        } catch (error) {
            console.error('Ошибка инициализации распознавания речи:', error);
            if (subtitlesText) subtitlesText.textContent = 'Распознавание не запустилось. Разрешите микрофон.';
            alert('Не удалось запустить распознавание. 1) Разрешите доступ к микрофону при запросе. 2) В Chrome распознавание работает только по HTTPS (или localhost).');
        }
    }

    // Функция остановки распознавания речи
    function stopSpeechRecognition() {
        isRecognizing = false;
        if (recognition) {
            recognition.stop();
            recognition = null;
        }
        if (startSpeechBtn) {
            startSpeechBtn.textContent = 'Распознавание';
            startSpeechBtn.classList.remove('active');
        }
        if (startSpeechBtnSubtitle) {
            startSpeechBtnSubtitle.textContent = 'Распознавание';
            startSpeechBtnSubtitle.classList.remove('active');
        }
        console.log('Распознавание речи остановлено');
    }

    // Обе кнопки запускают распознавание (в блоке камеры и в блоке субтитров)
    if (startSpeechBtn) {
        startSpeechBtn.addEventListener('click', startSpeechRecognition);
    }
    if (startSpeechBtnSubtitle) {
        startSpeechBtnSubtitle.addEventListener('click', startSpeechRecognition);
    }

    // Остановить распознавание при закрытии страницы
    window.addEventListener('beforeunload', stopSpeechRecognition);

    // Экспортировать функции для внешнего использования
    window.startSpeechRecognition = startSpeechRecognition;
    window.stopSpeechRecognition = stopSpeechRecognition;

    // Ученики: опрос субтитров учителя; по словам из субтитров ставить видео в очередь
    if (typeof currentUserRole !== 'undefined' && currentUserRole === 'student' && typeof lessonAccessCode !== 'undefined' && lessonAccessCode) {
        var lastSubtitleTimestamp = null;
        var lastEnqueuedSubtitleLength = 0;
        setInterval(function () {
            var url = lastSubtitleTimestamp ? '/api/lesson/' + lessonAccessCode + '/teacher-subtitle?last_timestamp=' + encodeURIComponent(lastSubtitleTimestamp) : '/api/lesson/' + lessonAccessCode + '/teacher-subtitle';
            fetch(url)
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    if (data.success && data.text != null) {
                        if (subtitlesText) subtitlesText.textContent = data.text;
                        if (subtitlesContainer) {
                            if (data.text) subtitlesContainer.classList.add('visible');
                            else subtitlesContainer.classList.remove('visible');
                        }
                        if (data.timestamp) lastSubtitleTimestamp = data.timestamp;
                        if (data.text && data.text.length > lastEnqueuedSubtitleLength) {
                            var newPart = data.text.slice(lastEnqueuedSubtitleLength);
                            lastEnqueuedSubtitleLength = data.text.length;
                            enqueueVideosFromText(newPart);
                        }
                    }
                })
                .catch(function () {
                });
        }, 500);
    }
}

// Управление списком учеников
function initializeStudents() {
    const studentsToggleBtn = document.getElementById('studentsToggleBtn');
    const closeStudentsBtn = document.getElementById('closeStudentsBtn');
    const studentsPanel = document.getElementById('studentsPanel');
    const studentsList = document.getElementById('studentsList');

    if (!studentsToggleBtn || !studentsPanel || !studentsList) {
        return; // Элементы не найдены
    }

    // Если есть access_code, присоединиться к уроку (для учеников)
    if (typeof lessonAccessCode !== 'undefined' && lessonAccessCode) {
        // Попытка присоединиться к уроку через API
        fetch(`/api/lesson/${lessonAccessCode}/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).catch(error => {
            console.log('Не удалось присоединиться через API (возможно, уже присоединен)');
        });
    }

    // Функция загрузки списка учеников
    function loadStudents() {
        if (typeof lessonAccessCode === 'undefined' || !lessonAccessCode) {
            if (studentsList) {
                studentsList.innerHTML = '<div class="no-students">Нет данных о уроке</div>';
            }
            return;
        }

        fetch(`/api/lesson/${lessonAccessCode}/students`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.students) {
                    displayStudents(data.students);
                } else {
                    if (studentsList) {
                        studentsList.innerHTML = '<div class="no-students">Ошибка загрузки списка учеников</div>';
                    }
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки учеников:', error);
                if (studentsList) {
                    studentsList.innerHTML = '<div class="no-students">Ошибка загрузки</div>';
                }
            });
    }

    // Функция отображения списка учеников
    function displayStudents(students) {
        if (!studentsList) return;

        if (!students || students.length === 0) {
            studentsList.innerHTML = '<div class="no-students">Нет присоединившихся учеников</div>';
            // Обновить счетчик на кнопке
            if (studentsToggleBtn) {
                studentsToggleBtn.innerHTML = 'Участники <span class="students-count">0</span>';
            }
            return;
        }

        studentsList.innerHTML = '';
        students.forEach(student => {
            const studentItem = document.createElement('div');
            studentItem.className = 'student-item';

            const avatar = document.createElement('div');
            avatar.className = 'student-avatar';
            avatar.textContent = student.username.charAt(0).toUpperCase();

            const info = document.createElement('div');
            info.className = 'student-info';
            const name = document.createElement('div');
            name.className = 'student-name';
            name.textContent = student.username;
            const email = document.createElement('div');
            email.className = 'student-email';
            email.textContent = student.email;

            info.appendChild(name);
            info.appendChild(email);

            studentItem.appendChild(avatar);
            studentItem.appendChild(info);

            studentsList.appendChild(studentItem);
        });

        // Обновить счетчик на кнопке
        if (studentsToggleBtn) {
            const count = students.length;
            studentsToggleBtn.innerHTML = 'Участники <span class="students-count">' + count + '</span>';
        }
    }

    // Экспортировать функцию для использования вне
    window.loadStudents = loadStudents;

    // Обработчики событий
    if (studentsToggleBtn) {
        studentsToggleBtn.addEventListener('click', function () {
            studentsPanel.style.display = studentsPanel.style.display === 'none' ? 'block' : 'none';
            if (studentsPanel.style.display === 'block') {
                loadStudents();
                // Автообновление каждые 3 секунды
                if (window.studentsUpdateInterval) {
                    clearInterval(window.studentsUpdateInterval);
                }
                window.studentsUpdateInterval = setInterval(loadStudents, 3000);
            } else {
                if (window.studentsUpdateInterval) {
                    clearInterval(window.studentsUpdateInterval);
                }
            }
        });
    }

    if (closeStudentsBtn) {
        closeStudentsBtn.addEventListener('click', function () {
            studentsPanel.style.display = 'none';
            if (window.studentsUpdateInterval) {
                clearInterval(window.studentsUpdateInterval);
            }
        });
    }

    // Загрузить список учеников при загрузке страницы
    loadStudents();
    // Автообновление каждые 5 секунд (даже если панель закрыта, для обновления счетчика)
    if (window.studentsAutoUpdateInterval) {
        clearInterval(window.studentsAutoUpdateInterval);
    }
    window.studentsAutoUpdateInterval = setInterval(loadStudents, 5000);
}

// Инициализация тестов в заданиях: опции без правильного ответа, показ правильного только после отправки
function initializeTaskTests() {
    document.querySelectorAll('.task-test').forEach(function (block) {
        const optionsJson = block.getAttribute('data-options');
        const correctRaw = block.getAttribute('data-correct');
        let options = [];
        try {
            options = JSON.parse(optionsJson || '[]');
        } catch (e) {
        }
        if (!Array.isArray(options)) options = [];
        const optionsEl = block.querySelector('.task-test-options');
        const submitBtn = block.querySelector('.task-test-submit');
        const resultEl = block.querySelector('.task-test-result');
        if (!optionsEl || !submitBtn) return;

        const name = 'task-' + (block.closest('.task-item') && block.closest('.task-item').getAttribute('data-task-id') || Math.random().toString(36).slice(2));
        options.forEach(function (opt, idx) {
            const text = typeof opt === 'object' && opt !== null ? (opt.text || opt.label || String(opt)) : String(opt);
            const label = document.createElement('label');
            label.className = 'task-test-option-label';
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = name;
            radio.value = String(idx);
            label.appendChild(radio);
            label.appendChild(document.createTextNode(' ' + text));
            optionsEl.appendChild(label);
        });

        function getOptionText(opt, idx) {
            return typeof opt === 'object' && opt !== null ? (opt.text || opt.label || String(opt)) : String(opt);
        }

        function getCorrectIndex() {
            if (correctRaw === null || correctRaw === '') return null;
            const num = parseInt(correctRaw, 10);
            if (!isNaN(num) && options[num] !== undefined) return String(num);
            const correctStr = String(correctRaw).trim();
            const found = options.findIndex(function (o) {
                return getOptionText(o, 0) === correctStr;
            });
            return found >= 0 ? String(found) : null;
        }

        const correctIndex = getCorrectIndex();
        const correctValue = correctIndex !== null && options[parseInt(correctIndex, 10)] !== undefined
            ? getOptionText(options[parseInt(correctIndex, 10)], 0) : null;

        submitBtn.addEventListener('click', function () {
            const selected = block.querySelector('input[name="' + name + '"]:checked');
            const selectedIndex = selected ? selected.value : null;
            const isCorrect = correctIndex !== null && selectedIndex === correctIndex;
            resultEl.style.display = 'block';
            resultEl.innerHTML = isCorrect
                ? '<span style="color: var(--success);">Правильно</span>'
                : '<span style="color: var(--danger);">Неправильно.</span> ' + (correctValue != null ? 'Правильный ответ: ' + correctValue : '');
        });
    });
}

// Когда документ готов
document.addEventListener('DOMContentLoaded', function () {
    // Задания-тесты: рендер опций, показ правильного ответа только после отправки
    initializeTaskTests();

    // Загрузить список видео жестов
    loadGestureVideos();

    // Инициализировать камеру
    initializeCamera();

    // Инициализировать распознавание речи
    initializeSpeechRecognition();

    // Инициализировать список учеников
    initializeStudents();

    // Видео жестов — только по субтитрам (параграфтан авто-кезек алынбайды)

    // Запустить чат
    initializeChat();

    // Проверять новое видео от сервера каждую секунду (для синхронизации между участниками)
    setInterval(checkForNewGestureVideo, 1000);

    // Текст урока (параграф): сохранить оригинал только для подсветки слова. Видео — только по субтитрам.
    if (typeof lessonData !== 'undefined' && lessonData.description) {
        originalLessonParagraphText = lessonData.description;
    }
});

// Функция преобразования текста в упрощенный формат для языка жестов
function simplifyTextForSignLanguage(text) {
    if (!text || text.trim().length === 0) return '';

    // Определить язык текста (простая проверка по кириллице/латинице)
    const isRussian = /[а-яё]/i.test(text);

    // 1-қадам: Разбить текст на предложения
    let sentences = text
        .split(/[.!?]+/)
        .map(s => s.trim())
        .filter(s => s.length > 0);

    // Слова для удаления (2-қадам)
    const wordsToRemove = isRussian ? [
        // Русские слова
        'потому что', 'поэтому', 'так как',
        'однако', 'возможно', 'может быть',
        'очень', 'сильно',
        'так', 'таким образом', 'это',
        'этот', 'тот',
        'по моему мнению', 'я думаю',
        'то есть', 'иными словами',
        'то', 'это', 'этот',
        'который', 'которая', 'которое', 'которые',
        'где', 'когда', 'как', 'что'
    ] : [
        // Казахские слова
        'себебі', 'сондықтан', 'өйткені',
        'дегенмен', 'мүмкін', 'бәлкім',
        'өте', 'қатты',
        'сонда', 'осылай', 'осы',
        'бұл', 'сол',
        'меніңше', 'менің ойымша',
        'яғни', 'яғниша',
        'сон', 'осы', 'бұл'
    ];

    // Замены абстрактных слов на конкретные (4-қадам)
    const abstractReplacements = isRussian ? {
        // Русские замены
        'настроение': 'состояние',
        'мысль': 'действие',
        'чувство': 'состояние',
        'было трудно': 'не понял',
        'трудно': 'не понял',
        'хорошо': 'правильно',
        'плохо': 'неправильно',
        'будет помогать': 'помогает',
        'говорил': 'сказал',
        'пошел': 'пошел',
        'пришел': 'пришел',
        'изучались': 'изучали',
        'обсуждались': 'обсуждали',
        'организованных': 'организовал',
        'вступил': 'вступил',
        'вернуться': 'вернулся',
        'разрешено': 'разрешили',
        'любил': 'любил',
        'сыграл': 'сыграл',
        'помог': 'помог',
        'найти': 'нашел',
        'писала': 'написала',
        'переживал': 'чувствовал'
    } : {
        // Казахские замены
        'көңіл-күйім': 'күйім',
        'көңіл-күй': 'күй',
        'ой': 'әрекет',
        'сезім': 'күй',
        'қиын болды': 'түсінбедім',
        'қиын': 'түсінбедім',
        'жақсы': 'дұрыс',
        'жаман': 'дұрыс емес',
        'көмектесетін болады': 'көмектеседі',
        'сөйлесіп отыр едім': 'сөйлестім',
        'бардым': 'бардым',
        'келдім': 'келдім'
    };

    let result = [];

    sentences.forEach(sentence => {
        let s = sentence.trim();

        // 2-қадам: Удалить лишние слова
        wordsToRemove.forEach(word => {
            const regex = new RegExp('\\b' + word + '\\b', 'gi');
            s = s.replace(regex, '');
        });

        // 4-қадам: Заменить абстрактные слова
        Object.keys(abstractReplacements).forEach(abstract => {
            const regex = new RegExp(abstract.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
            s = s.replace(regex, abstractReplacements[abstract]);
        });

        // Упростить множественные пробелы
        s = s.replace(/\s+/g, ' ').trim();

        if (s.length === 0) return;

        // 1-қадам: Если предложение слишком длинное, разбить его
        if (s.length > 50) {
            // Попробовать разбить по запятым
            const parts = s.split(',').map(p => p.trim()).filter(p => p.length > 0);
            if (parts.length > 1 && parts.every(p => p.length < 50)) {
                result.push(...parts);
                return;
            }

            // Разбить по союзам
            const conjunctions = isRussian ?
                ['и', 'а', 'но', 'однако', 'или', 'либо', 'также', 'тоже'] :
                ['және', 'мен', 'бен', 'пен', 'да', 'де', 'та', 'те'];
            for (let conj of conjunctions) {
                if (s.includes(' ' + conj + ' ') || s.startsWith(conj + ' ')) {
                    const parts = s.split(new RegExp('\\s+' + conj + '\\s+', 'gi'))
                        .map(p => p.trim())
                        .filter(p => p.length > 0);
                    if (parts.length > 1) {
                        result.push(...parts);
                        return;
                    }
                }
            }
        }

        // 5-қадам: Одно предложение = одна мысль
        // Если есть несколько действий, разделить
        const actionWords = isRussian ?
            ['пошел', 'пришел', 'ушел', 'написал', 'прочитал', 'сделал', 'сказал', 'вступил', 'вернулся', 'изучали', 'обсуждали', 'любил', 'сыграл', 'помог', 'нашел', 'написала', 'чувствовал'] :
            ['бардым', 'келдім', 'кеттім', 'жаздым', 'оқыдым', 'жасадым'];
        let actionCount = 0;
        actionWords.forEach(action => {
            if (s.includes(action)) actionCount++;
        });

        if (actionCount > 1) {
            // Разделить по действиям
            const actionPattern = isRussian ?
                /(?=пошел|пришел|ушел|написал|прочитал|сделал|сказал|вступил|вернулся|изучали|обсуждали|любил|сыграл|помог|нашел|написала|чувствовал)/gi :
                /(?=бардым|келдім|кеттім|жаздым|оқыдым|жасадым)/gi;
            const parts = s.split(actionPattern)
                .map(p => p.trim())
                .filter(p => p.length > 0);
            if (parts.length > 1) {
                result.push(...parts);
                return;
            }
        }

        result.push(s);
    });

    // 6-қадам: Упростить глаголы
    result = result.map(s => {
        if (isRussian) {
            // Упростить русские глаголы
            s = s.replace(/будет\s+(\w+)/gi, '$1');
            s = s.replace(/(\w+)ся/gi, '$1');
            s = s.replace(/было\s+(\w+)/gi, '$1');
            s = s.replace(/были\s+(\w+)/gi, '$1');
        } else {
            // Упростить казахские глаголы
            s = s.replace(/ететін болады/gi, 'етеді');
            s = s.replace(/етіп отыр/gi, 'етеді');
            s = s.replace(/етіп жатқан/gi, 'етеді');
            s = s.replace(/еткен болады/gi, 'етті');
            s = s.replace(/етіп тұр/gi, 'етеді');
            s = s.replace(/етіп жүр/gi, 'етеді');
        }

        // Упростить множественные пробелы
        s = s.replace(/\s+/g, ' ').trim();
        return s;
    }).filter(s => s.length > 0);

    // 7-қадам: Упростить вопросы
    result = result.map(s => {
        // Упростить структуру вопроса
        if (s.match(/ба\s*$/i) || s.match(/ма\s*$/i) || s.match(/ме\s*$/i) || s.match(/па\s*$/i) || s.match(/пе\s*$/i)) {
            // Убрать лишние слова из вопроса
            s = s.replace(/\s+(ба|ма|ме|па|пе)\s*$/i, '?');
        }
        return s.trim();
    }).filter(s => s.length > 0);

    // 8-қадам: Финальная проверка и очистка
    result = result.map(s => {
        // Убрать одиночные буквы и очень короткие слова
        s = s.replace(/\b\w{1}\b/g, '');
        // Убрать множественные пробелы
        s = s.replace(/\s+/g, ' ').trim();
        return s;
    }).filter(s => s.length > 2); // Минимум 3 символа

    // Убрать дубликаты
    result = [...new Set(result)];

    // Объединить результат (каждое предложение с новой строки)
    if (result.length === 0) return '';
    return result.join('.\n') + '.';
}

// Функция автоматического воспроизведения видео жестов на основе упрощенного текста
let simplifiedTextPlaybackQueue = [];
let isPlayingSimplifiedText = false;

function playSimplifiedTextGestures(simplifiedText) {
    console.log('playSimplifiedTextGestures вызвана с текстом:', simplifiedText);
    if (!simplifiedText || simplifiedText.trim().length === 0) {
        console.log('Текст пуст, выход');
        return;
    }
    if (gestureVideosList.length === 0) {
        console.log('Список видео жестов еще не загружен, попробуем позже... Загружено видео:', gestureVideosList.length);
        // Попробовать еще раз через 2 секунды
        setTimeout(() => {
            if (gestureVideosList.length > 0) {
                console.log('Повторная попытка, видео загружено:', gestureVideosList.length);
                playSimplifiedTextGestures(simplifiedText);
            } else {
                console.log('Видео все еще не загружено');
                // Продолжить даже без видео, чтобы показать эмодзи жесты
            }
        }, 2000);
        // Не возвращаемся, продолжаем обработку даже без видео
    } else {
        console.log('Загружено видео жестов:', gestureVideosList.length);
    }

    // Разбить упрощенный текст на предложения/фразы
    const phrases = simplifiedText
        .split(/[.\n]+/)
        .map(p => p.trim())
        .filter(p => p.length > 0);

    if (phrases.length === 0) return;

    // Очистить очередь
    simplifiedTextPlaybackQueue = [];

    // Для каждой фразы найти соответствующее видео
    phrases.forEach((phrase, index) => {
        // Убрать точку в конце, если есть
        const cleanPhrase = phrase.replace(/\.+$/, '').trim();
        if (cleanPhrase.length === 0) return;

        // Разбить фразу на слова
        const words = cleanPhrase.split(/\s+/).filter(w => w.length > 0);

        // Для каждого слова найти видео отдельно
        words.forEach((word, wordIndex) => {
            // Убрать знаки препинания
            const cleanWord = word.replace(/[.,!?;:()\[\]{}]/g, '').trim();
            if (cleanWord.length < 2) return; // Игнорировать очень короткие слова

            // Искать видео для слова
            const wordVideo = findGestureVideo(cleanWord);

            console.log(`Слово: "${cleanWord}", видео найдено:`, wordVideo ? wordVideo.text : 'нет');

            // Добавить в очередь (даже если видео не найдено, чтобы показать эмодзи)
            simplifiedTextPlaybackQueue.push({
                phrase: cleanWord,
                video: wordVideo,
                index: index * 1000 + wordIndex
            });
        });
    });

    // Сортировать очередь по индексу
    simplifiedTextPlaybackQueue.sort((a, b) => a.index - b.index);

    // Начать воспроизведение очереди
    if (simplifiedTextPlaybackQueue.length > 0 && !isPlayingSimplifiedText) {
        console.log('Начинаем воспроизведение жестов для упрощенного текста. Всего элементов в очереди:', simplifiedTextPlaybackQueue.length);
        playNextSimplifiedGesture();
    } else {
        console.log('Очередь пуста или уже воспроизводится');
    }
}

// Функция воспроизведения следующего жеста из очереди
function playNextSimplifiedGesture() {
    if (simplifiedTextPlaybackQueue.length === 0) {
        isPlayingSimplifiedText = false;
        clearLessonParagraphHighlight();
        return;
    }

    isPlayingSimplifiedText = true;
    const item = simplifiedTextPlaybackQueue.shift();

    // Подсветить текущее слово в параграфе урока синим (пока идёт видео)
    highlightWordInLessonParagraph(item.phrase);

    if (item.video) {
        // Есть видео - воспроизвести его
        const gestureVideo = document.getElementById('gestureVideo');

        if (gestureVideo) {
            // Обработчик окончания видео
            const onVideoEnd = function () {
                gestureVideo.removeEventListener('ended', onVideoEnd);
                // Небольшая пауза перед следующим жестом
                setTimeout(() => {
                    playNextSimplifiedGesture();
                }, 500);
            };

            gestureVideo.addEventListener('ended', onVideoEnd);
            playGestureVideo(item.video, false);
        } else {
            // Если видео элемент не найден, просто перейти к следующему
            setTimeout(() => {
                playNextSimplifiedGesture();
            }, 2000);
        }
    } else {
        // Нет видео — показать только текст фразы; слово в параграфе уже подсвечено
        const gestureContent = document.getElementById('gestureContent');
        const wordDisplay = document.getElementById('word-display');
        const gestureVideo = document.getElementById('gestureVideo');
        if (gestureContent) gestureContent.style.display = 'flex';
        if (gestureVideo) gestureVideo.style.display = 'none';
        if (wordDisplay) wordDisplay.textContent = item.phrase;
        const gestureDisplay = document.getElementById('gesture-display');
        if (gestureDisplay) gestureDisplay.textContent = '';
        setTimeout(function () {
            playNextSimplifiedGesture();
        }, 1500);
    }
}

// Когда очередь пуста — убрать подсветку слова в параграфе
function clearLessonParagraphHighlight() {
    var p = document.getElementById('lesson-description-p');
    if (p && originalLessonParagraphText) {
        p.textContent = originalLessonParagraphText;
    }
}
