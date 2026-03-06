// static/script.js
let i18n = {};
function translatePage(lang) {
    fetch(`/api/auth/language?lang=${lang}`)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
            return res.json();
        })
        .then(data => {
            Object.assign(i18n, data.translations); // Use data.translations since the backend returns {translations, language}
            document.querySelectorAll('[data-i18n]').forEach(el => {
                el.textContent = i18n[el.dataset.i18n] || el.dataset.i18n;
            });
        })
        .catch(err => {
            console.error('Translation failed:', err);
            alert('Failed to load translations. Using default English. Check console for details.');
            // Fallback to default English if translation fails
            if (lang !== 'en') translatePage('en');
        });
}

document.addEventListener('DOMContentLoaded', () => {
    // Load default language (English)
    fetch('/api/auth/language?lang=en')
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
            return res.json();
        })
        .then(data => {
            Object.assign(i18n, data.translations); // Use data.translations
            translatePage('en');
        })
        .catch(err => {
            console.error('Initial translation failed:', err);
            alert('Initial translation failed. Using default text. Check console for details.');
        });

    // Smooth Scroll for Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Animate Elements on Scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-slideIn');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.card').forEach(card => observer.observe(card));
});

// static/script.js
function findFacilities() {
    const facilitiesDiv = document.getElementById('facilities');
    facilitiesDiv.innerHTML = '<p class="text-indigo-600">Fetching your location...</p>';

    if (!navigator.geolocation) {
        facilitiesDiv.innerHTML = '<p class="text-red-600">Geolocation is not supported by your browser. Using a fallback location for testing...</p>';
        console.warn('Geolocation not supported');

        // Fallback location (Ahmedabad, Gujarat: 23.0225, 72.5714)
        fetchFacilities(23.0225, 72.5714);
        return;
    }

    navigator.geolocation.getCurrentPosition(
        position => {
            const { latitude, longitude } = position.coords;
            facilitiesDiv.innerHTML = '<p class="text-indigo-600">Location detected! Fetching nearby facilities...</p>';
            fetchFacilities(latitude, longitude);
        },
        error => {
            let errorMessage = '';
            switch (error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = 'Location access denied. Using a fallback location for testing...';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = 'Location information is unavailable. Using a fallback location for testing...';
                    break;
                case error.TIMEOUT:
                    errorMessage = 'The request to get your location timed out. Using a fallback location for testing...';
                    break;
                default:
                    errorMessage = 'An unknown error occurred while fetching your location. Using a fallback location for testing...';
            }
            facilitiesDiv.innerHTML = `<p class="text-yellow-600">${errorMessage}</p>`;
            console.error('Geolocation error:', error.message);

            // Fallback location (Ahmedabad, Gujarat: 23.0225, 72.5714)
            fetchFacilities(23.0225, 72.5714);
        },
        { timeout: 10000, enableHighAccuracy: true }
    );
}
// Voice Input for MamaBot
function startVoiceInput() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-IN'; // Default to English (India), can be dynamic based on user language
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();
    document.getElementById('chatbot-response').innerHTML = '<p class="text-indigo-600">Listening...</p>';

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('chatbot-input').value = transcript;
        document.getElementById('chatbot-response').innerHTML = '<p class="text-indigo-600">You said: ' + transcript + '</p>';
        sendChatbotQuery(); // Automatically send the query after voice input
    };

    recognition.onerror = (event) => {
        document.getElementById('chatbot-response').innerHTML = '<p class="text-red-600">Voice input error: ' + event.error + '</p>';
    };
}

// Voice Output for MamaBot Response
function speakResponse() {
    const responseText = document.getElementById('chatbot-response').textContent.replace('MamaBot: ', '');
    if (!responseText || responseText.includes('Thinking...') || responseText.includes('Error')) {
        alert('No valid response to speak. Please ask a question first.');
        return;
    }

    const utterance = new SpeechSynthesisUtterance(responseText);
    utterance.lang = 'en-IN'; // Match with user language
    utterance.pitch = 1;
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
}
function fetchFacilities(latitude, longitude) {
    const facilitiesDiv = document.getElementById('facilities');
    axios.get(`/api/health/facilities?lat=${latitude}&lon=${longitude}`)
        .then(res => {
            if (res.data.facilities && res.data.facilities.length > 0) {
                facilitiesDiv.innerHTML = res.data.facilities
                    .map(f => `<p class="text-indigo-800">${f.name || 'Unnamed Facility'} (${f.distance ? f.distance + 'km' : 'Unknown distance'}) - ${f.address || 'No address'}</p>`)
                    .join('');
            } else {
                facilitiesDiv.innerHTML = '<p class="text-yellow-600">No healthcare facilities found nearby. Try increasing the search radius or using a different location.</p>';
            }
        })
        .catch(err => {
            facilitiesDiv.innerHTML = '<p class="text-red-600">Error fetching facilities: ' + (err.response?.data?.msg || err.message) + '</p>';
            console.error('Facilities fetch failed:', err);
        });
}

function callASHA() {
    alert('Calling ASHA: Contact your local health worker at 104.');
}

function learnMore() {
    window.open('https://www.mayoclinic.org/healthy-lifestyle/pregnancy-week-by-week/in-depth/pregnancy-nutrition/art-20045082', '_blank');
}

async function sendChatbotQuery() {
    const input = document.getElementById('chatbot-input').value.trim();
    const responseDiv = document.getElementById('chatbot-response');

    if (!input) {
        responseDiv.innerHTML = '<p class="text-red-600">Please enter a question to ask MamaBot.</p>';
        return;
    }

    responseDiv.innerHTML = '<p class="text-indigo-600">Asking MamaBot...</p>';

    try {
        const res = await axios.post('/api/chatbot/query', {
            message: input,
            user_type: 'Pregnant Woman'
        }, {
            headers: {'Content-Type': 'application/json'}
        });
        responseDiv.innerHTML = `<p class="text-indigo-800">${res.data.reply || 'No response from MamaBot.'}</p>`;
        document.getElementById('chatbot-input').value = '';
    } catch (err) {
        const errorMsg = err.response?.data?.msg || err.message || 'Failed to get a response from MamaBot.';
        responseDiv.innerHTML = `<p class="text-red-600">Error: ${errorMsg}</p>`;
        console.error('Chatbot request failed:', err);

        // Fallback to dummy chatbot
        const dummyResponse = getDummyChatbotResponse(input);
        responseDiv.innerHTML = `<p class="text-indigo-800">[Dummy Response] ${dummyResponse}</p>`;
    }
}

// Dummy Chatbot Responses
function getDummyChatbotResponse(message) {
    const lowerMessage = message.toLowerCase();
    const responses = {
        "ifa tablets": "Hi! You should take IFA (Iron and Folic Acid) tablets daily, preferably after a meal, to prevent anemia during pregnancy. Consult your doctor for the exact dosage.",
        "antenatal visits": "You should attend at least 4 antenatal visits during pregnancy: at 12, 20, 28, and 36 weeks. These visits help monitor your health and your baby’s development.",
        "vaccinations": "For your child, ensure they receive the BCG, OPV, and Hepatitis B vaccines at birth, followed by DPT, Hib, and Rotavirus vaccines at 6, 10, and 14 weeks.",
        "nutrition": "Eat a balanced diet with proteins (dal, eggs), iron-rich foods (spinach, jaggery), and calcium (milk, yogurt). Avoid raw or undercooked foods during pregnancy.",
        "emergency": "In case of an emergency (e.g., severe bleeding, abdominal pain), call 104 or visit the nearest health center immediately."
    };

    for (const keyword in responses) {
        if (lowerMessage.includes(keyword)) {
            return responses[keyword];
        }
    }
    return "I’m not sure about that. Please ask about IFA tablets, antenatal visits, vaccinations, nutrition, or emergencies, or consult your local health worker.";
}