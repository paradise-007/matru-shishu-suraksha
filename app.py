from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from transformers import AutoModelForQuestionAnswering, AutoTokenizer
from flask_caching import Cache
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from google.generativeai import GenerativeModel
import logging
import requests
import math
import pymongo
import bcrypt
from functools import wraps
from flask import abort
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from datasets import load_dataset
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bson.objectid import ObjectId
from flask_cors import CORS
import os
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
MONGO_URI = os.getenv("MONGO_URI")
# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.urandom(24)  # Secure secret key
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
CORS(app)

# Cache configuration
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = pymongo.MongoClient(app.config['MONGO_URI'])
    db = client.get_default_database()
    users_collection = db.users
    health_collection = db.health
    feedback_collection = db.feedback
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    raise e

# LocationIQ API Key
HF_API_TOKEN  = os.getenv("HF_API_TOKEN ")

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

if not EMAIL_USER or not EMAIL_PASS:
    raise ValueError("EMAIL_USER or EMAIL_PASS not found in .env file. Check your .env configuration.")

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not GEMINI_API_KEY or not GOOGLE_MAPS_API_KEY:
    logger.error("GEMINI_API_KEY or GOOGLE_MAPS_API_KEY not found in .env file. Please set them.")
    raise ValueError("GEMINI_API_KEY and GOOGLE_MAPS_API_KEY are required.")

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
available_models = [m.name for m in genai.list_models()]
logger.info(f"Available models: {available_models}")

gemini_model = None
try:
    gemini_model = GenerativeModel(model_name="gemini-1.5-pro-latest")
    logger.info("Gemini model loaded successfully")
except Exception as e:
    logger.warning(f"Gemini model loading failed: {e}. Falling back to local model only.")
    gemini_model = None

# Load pretrained conversational model and tokenizer
try:
    model_path = "./conversational_model"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    logger.info("Pre-trained conversational model and tokenizer loaded from ./conversational_model")
except Exception as e:
    logger.error(f"Failed to load pre-trained model or tokenizer: {e}")
    raise e

# Conversational Inference
def get_conversational_response(message, context=""):
    try:
        generator = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=50)
        full_input = f"Context: {context}. Question: {message}\nAnswer:" if context else f"Question: {message}\nAnswer:"
        response = generator(full_input, pad_token_id=tokenizer.eos_token_id)
        answer = response[0]['generated_text'].split("Answer:")[-1].strip()
        logger.info(f"Conversational Response for '{message}': {answer}")
        return answer if answer else "No response generated."
    except Exception as e:
        logger.error(f"Conversational inference error: {e}")
        return "Error processing question. Try again."

    # Fall back to Gemini API if conversational model fails and Gemini is available
    if not answer or answer == "No response generated." and gemini_model:
        try:
            prompt = f"Provide maternal or child health advice based on the following context: {context}. Question: {message}. Answer in a concise, supportive tone, referencing India’s health guidelines where applicable."
            gemini_response = gemini_model.generate_content(prompt, stream=False)
            answer = gemini_response.text if gemini_response else "No response from Gemini. Please try again."
            logger.info(f"Gemini Response for '{message}': {answer}")
            return answer
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "Error processing request. Consult a healthcare worker."
    return answer

translations = {
    'en': {
        'login': 'Login', 'register': 'Register', 'onboarding': 'Onboarding',
        'pregnancySetup': 'Pregnancy Setup', 'motherSetup': 'Mother Setup',
        'caregiverSetup': 'Caregiver Setup', 'pregnancyHealth': 'Pregnancy Health',
        'childHealth': 'Child Health', 'healthAssessment': 'Health Assessment',
        'resources': 'Resources', 'progress': 'Progress Tracking', 'dashboard': 'Dashboard',
        'findFacilities': 'Find Nearby Facilities', 'callASHA': 'Call ASHA', 'learnMore': 'Learn More',
        'askMamaBot': 'Ask MamaBot', 'send': 'Send',
        'vaccinationSchedule': 'Vaccination Schedule',
        'vaccinationNote': 'Note: Schedule is based on India\'s Universal Immunization Programme. Consult your health worker for updates.',
        'malnutritionSection': 'Child Malnutrition Assessment',
        'ageMonths': 'Age (months)',
        'sex': 'Sex',
        'weightKg': 'Weight (kg)',
        'assessMalnutrition': 'Assess Malnutrition'
    },
    'gu': {
        'login': 'લૉગિન', 'register': 'નોંધણી', 'onboarding': 'ઓનબોર્ડિંગ',
        'pregnancySetup': 'ગર્ભાવસ્થા સેટઅપ', 'motherSetup': 'માતા સેટઅપ',
        'caregiverSetup': 'સંભાલ રાખનાર સેટઅપ', 'pregnancyHealth': 'ગર્ભાવસ્થા આરોગ્ય',
        'childHealth': 'બાળ આરોગ્ય', 'healthAssessment': 'આરોગ્ય મૂલ્યાંકન',
        'resources': 'સંસાધનો', 'progress': 'પ્રગતિ ટ્રેકિંગ', 'dashboard': 'ડેશબોર્ડ',
        'findFacilities': 'નજીકની સુવિધાઓ શોધો', 'callASHA': 'આશા કાર્યકરને કૉલ કરો',
        'learnMore': 'વધુ જાણો', 'askMamaBot': 'મામાબોટને પૂછો', 'send': 'મોકલો',
        'vaccinationSchedule': 'રસીકરણ સમયપત્રક',
        'vaccinationNote': 'નોંધ: સમયપત્રક ભારતની યુનિવર્સલ ઇમ્યુનાઇઝેશન પ્રોગ્રામ પર આધારિત છે. તમારા આરોગ્ય કર્મચારીને સલાહ લો.',
        'malnutritionSection': 'બાળ માલન્યુટ્રિશન મૂલ્યાંકન',
        'ageMonths': 'ઉંમર (મહિના)',
        'sex': 'લિંગ',
        'weightKg': 'વજન (કિ.ગ્રા.)',
        'assessMalnutrition': 'માલન્યુટ્રિશનનું મૂલ્યાંકન કરો'
    }
}

HEALTH_RESPONSES = {
    "ifa tablets": {
        "primary": "Take IFA tablets daily after a meal (60 mg iron, 400 mcg folic acid) from the second trimester for 100+ days. Consult your doctor for side effects like nausea.",
        "related": [
            "Ensure you attend antenatal visits to monitor iron levels.",
            "Pair IFA with vitamin C-rich foods (e.g., oranges) to improve absorption.",
            "Contact your ASHA worker if you miss doses."
        ]
    },
    "antenatal visits": {
        "primary": "Attend 4 antenatal visits (12, 20, 28, 36 weeks). Bring your MCP card to government health centers for free checkups.",
        "related": [
            "Keep your vaccination schedule updated during visits.",
            "Ask about nutritional supplements at each visit.",
            "Call 104 for emergency transport to a health center."
        ]
    },
    "vaccinations during pregnancy": {
        "primary": "Get Tdap (27-36 weeks) and tetanus toxoid (2 doses, 4 weeks apart) during pregnancy. Consult your doctor.",
        "related": [
            "Ensure your child receives BCG at birth.",
            "Postpartum, consider flu and MMR vaccines.",
            "Free vaccines are available at government clinics."
        ]
    },
    "vaccinations post pregnancy": {
        "primary": "Get MMR and flu shots postpartum. Consult your doctor 6 weeks after delivery.",
        "related": [
            "Breastfeeding mothers should stay updated on vaccines.",
            "Check your child’s vaccination card at the 6-week checkup.",
            "Contact ASHA for reminders."
        ]
    },
    "child vaccinations": {
        "primary": "Follow India’s schedule: BCG, OPV, Hepatitis B at birth; DPT, Hib, Rotavirus at 6, 10, 14 weeks. Free at government centers.",
        "related": [
            "Monitor for fever after vaccines and consult a doctor.",
            "Visit Anganwadi centers for growth tracking.",
            "Keep a record of all vaccine dates."
        ]
    },
    "malnutrition in pregnancy": {
        "primary": "Eat proteins (dal, eggs), iron-rich foods (spinach), and calcium (milk). Get free supplements at Anganwadi centers.",
        "related": [
            "Avoid junk food to maintain a balanced diet.",
            "Check your weight during antenatal visits.",
            "Consult a nutritionist if symptoms persist."
        ]
    },
    "malnutrition in child": {
        "primary": "Breastfeed exclusively for 6 months, then add mashed dal, vegetables. Monitor growth at Anganwadi centers.",
        "related": [
            "Introduce fruits after 6 months for variety.",
            "Watch for signs like lethargy or thin limbs.",
            "Free nutritional support is available via ASHA."
        ]
    },
    "emergency": {
        "primary": "Call 104 or 108 for severe bleeding, pain, or labor issues. Keep your MCP card handy.",
        "related": [
            "Prepare a hospital bag in advance.",
            "Inform your family or ASHA worker during emergencies.",
            "Nearest facility details can be found on the app."
        ]
    },
    "postpartum care": {
        "primary": "Rest, eat balanced meals, and attend a 6-week checkup. Contact ASHA for support.",
        "related": [
            "Focus on pelvic floor exercises post-delivery.",
            "Monitor for signs of infection or depression.",
            "Join local mother support groups."
        ]
    },
    "breastfeeding": {
        "primary": "Feed on demand within 1 hour of birth. Consult a lactation specialist if painful.",
        "related": [
            "Ensure proper latch to avoid nipple soreness.",
            "Stay hydrated and eat nutrient-rich foods.",
            "Seek help from ASHA if supply is low."
        ]
    },
    "fetal development": {
        "primary": "Monitor growth with ultrasounds; report reduced movements after 28 weeks.",
        "related": [
            "Track kick counts daily after 28 weeks.",
            "Attend regular scans for fetal health.",
            "Consult a doctor for any concerns."
        ]
    },
    "mental health": {
        "primary": "Practice relaxation; seek help at 14416 if depressed.",
        "related": [
            "Join support groups for emotional well-being.",
            "Talk to your partner or family about feelings.",
            "Free counseling is available via helplines."
        ]
    },
    "dietary supplements": {
        "primary": "Take folic acid (400 mcg), IFA (60 mg iron), and calcium (1,000 mg) daily. Consult your doctor.",
        "related": [
            "Avoid taking supplements on an empty stomach.",
            "Check with your doctor for personalized doses.",
            "Free supplements are available at health centers."
        ]
    }
}

# Decorator for authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def calculate_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def fetch_health_api_response(query):
    try:
        url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        payload = {"inputs": query}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0]['generated_text'] if isinstance(data, list) and 'generated_text' in data[0] else None
    except Exception as e:
        logger.error(f"Hugging Face API error: {e}")
        return None

def generate_pregnancy_timeline(lmp_date):
    timeline = {}
    current_date = lmp_date
    for week in range(1, 41):
        start_day = current_date + timedelta(days=(week - 1) * 7)
        end_day = start_day + timedelta(days=6)
        timeline[f'Week {week} (Day {((week - 1) * 7) + 1} - Day {week * 7})'] = {
            'start': start_day.strftime('%Y-%m-%d'),
            'end': end_day.strftime('%Y-%m-%d')
        }
    return timeline

def generate_vaccination_schedule(edd):
    edd_date = datetime.strptime(edd, '%Y-%m-%d')
    lmp_date = edd_date - timedelta(days=280)  # Approximate LMP

    # Maternal vaccination schedule
    maternal_schedule = {
        'TT1 (First Dose)': (lmp_date + timedelta(weeks=12)).strftime('%Y-%m-%d'),
        'TT2 (Second Dose)': (lmp_date + timedelta(weeks=20)).strftime('%Y-%m-%d'),
        'TT Booster (if applicable)': (lmp_date + timedelta(weeks=28)).strftime('%Y-%m-%d'),
        'Influenza Vaccine': (lmp_date + timedelta(weeks=8)).strftime('%Y-%m-%d'),
        'COVID-19 Dose 1': (lmp_date + timedelta(weeks=20)).strftime('%Y-%m-%d'),
        'COVID-19 Dose 2': (lmp_date + timedelta(weeks=28)).strftime('%Y-%m-%d')
    }

    # Child vaccination schedule (post-birth, based on EDD)
    delivery_date = edd_date
    child_schedule = {
        'Birth (BCG, OPV, Hepatitis B)': delivery_date.strftime('%Y-%m-%d'),
        '6 Weeks (DPT, Hib, Rotavirus)': (delivery_date + timedelta(weeks=6)).strftime('%Y-%m-%d'),
        '10 Weeks (DPT, Hib, Rotavirus)': (delivery_date + timedelta(weeks=10)).strftime('%Y-%m-%d'),
        '14 Weeks (DPT, Hib, Rotavirus)': (delivery_date + timedelta(weeks=14)).strftime('%Y-%m-%d'),
        '9 Months (Measles, Vitamin A)': (delivery_date + timedelta(weeks=39)).strftime('%Y-%m-%d'),
        '16-24 Months (MMR, DPT Booster)': (delivery_date + timedelta(weeks=78)).strftime('%Y-%m-%d'),
        '5-6 Years (DT, OPV Booster)': (delivery_date + timedelta(weeks=260)).strftime('%Y-%m-%d')
    }

    # Calendar events format (compatible with FullCalendar)
    calendar_events = [
        {'title': vaccine, 'start': date, 'allDay': True}
        for vaccine, date in {**maternal_schedule, **child_schedule}.items()
    ]

    return {
        'maternal_vaccinations': maternal_schedule,
        'child_vaccinations': child_schedule,
        'pregnancy_timeline': generate_pregnancy_timeline(lmp_date),
        'calendar_events': calendar_events
    }

def notify_vaccination_schedule(email, schedule):
    try:
        user = health_collection.find_one({'email': email})
        if user:
            notifications = []
            today = datetime.utcnow().date()
            for event in schedule['calendar_events']:
                event_date = datetime.strptime(event['start'], '%Y-%m-%d').date()
                days_diff = (event_date - today).days
                if 0 <= days_diff <= 7:  # Notify for upcoming week
                    message = f"Vaccination reminder: {event['title']} due on {event['start']} (in {days_diff} days). Visit your health center."
                    notifications.append({'message': message, 'date': event['start'], 'read': False})
                    # Email setup
                    msg = MIMEText(message)
                    msg['Subject'] = 'Vaccination Reminder - Matru-Shishu Suraksha'
                    msg['From'] = os.getenv('EMAIL_USER')
                    msg['To'] = email

                    # Send email via Gmail SMTP
                    with smtplib.SMTP('smtp.gmail.com', 465) as server:
                        server.starttls()
                        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
                        server.send_message(msg)

            if notifications:
                health_collection.update_one(
                    {'email': email},
                    {'$push': {'notifications': {'$each': notifications}}},
                    upsert=True
                )
                logger.info(f"Notifications stored and emailed for {email}: {notifications}")
    except Exception as e:
        logger.error(f"Notification error: {e}")

# OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

@app.route('/callback')
def callback():
    flow = InstalledAppFlow.from_client_secrets_file('client.json', SCOPES)
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    return redirect(url_for('pregnancy_setup'))

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('client.json', SCOPES)
        creds = flow.run_local_server(port=3000) 
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('calendar', 'v3', credentials=creds)

def sync_to_google_calendar(email, schedule):
    service = get_calendar_service()
    user = health_collection.find_one({'email': email})
    if user:
        for event in schedule['calendar_events']:
            event_data = {
                'summary': event['title'],
                'start': {'date': event['start'], 'timeZone': 'UTC'},
                'end': {'date': event['start'], 'timeZone': 'UTC'},  # All-day event
                'reminders': {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 24 * 60}]},
            }
            try:
                service.events().insert(calendarId='primary', body=event_data).execute()
                logger.info(f"Added {event['title']} to Google Calendar for {email}")
            except Exception as e:
                logger.error(f"Failed to add {event['title']} to Google Calendar: {e}")

@app.route('/sync_google_calendar', methods=['POST'])
def sync_google_calendar():
    data = request.get_json()
    sync_to_google_calendar(data['email'], data['schedule'])
    logger.info(f"Sync response sent: {'Successfully synced with Google Calendar!'}")
    return jsonify({'msg': 'Successfully synced with Google Calendar!'})

@app.route('/pregnancy_setup', methods=['GET', 'POST'])
@login_required
def pregnancy_setup():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'msg': 'No data provided'}), 400

        health_collection.update_one(
            {'email': session['email']},
            {'$set': {
                'trimester': data.get('trimester'),
                'edd': data.get('edd'),
                'prevPregnancies': data.get('prevPregnancies'),
                'healthAccess': data.get('healthAccess'),
                'distance': data.get('distance'),
                'ashaRegistered': data.get('ashaRegistered'),
                'updated_at': datetime.utcnow()
            }},
            upsert=True
        )

        if data.get('edd'):
            schedule = generate_vaccination_schedule(data['edd'])
            health_collection.update_one(
                {'email': session['email']},
                {'$set': {'vaccination_schedule': schedule}},
                upsert=True
            )
            notify_vaccination_schedule(session['email'], schedule)
            return jsonify({
                'msg': 'Pregnancy setup and vaccination schedule saved successfully.',
                'redirect': url_for('pregnancy_setup'),
                'vaccination_schedule': schedule
            }), 200

        return jsonify({'msg': 'Pregnancy setup saved successfully.', 'redirect': url_for('pregnancy_setup')}), 200

    # Handle GET request
    user_data = health_collection.find_one({'email': session['email']})
    vaccination_schedule = user_data.get('vaccination_schedule', {}) if user_data else {}
    if not vaccination_schedule.get('calendar_events') and user_data and user_data.get('edd'):
        vaccination_schedule = generate_vaccination_schedule(user_data['edd'])
        health_collection.update_one(
            {'email': session['email']},
            {'$set': {'vaccination_schedule': vaccination_schedule}},
            upsert=True
        )
    elif not vaccination_schedule:
        vaccination_schedule = {'maternal_vaccinations': {}, 'child_vaccinations': {}, 'pregnancy_timeline': {}, 'calendar_events': []}
    return render_template('pregnancy_setup.html', vaccination_schedule=vaccination_schedule)
# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('login'))

        user = users_collection.find_one({'email': email})
        if user and bcrypt.checkpw(password.encode(), user['password']):
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['role'] = user.get('role', 'user')
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('userType')
        district = request.form.get('district')
        language = request.form.get('language')

        if not all([email, password, user_type, district, language]):
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if users_collection.find_one({'email': email}):
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user_data = {
            'email': email,
            'password': hashed_password,
            'role': user_type.lower(),
            'district': district,
            'language': language,
            'created_at': datetime.utcnow()
        }
        users_collection.insert_one(user_data)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        district = request.form.get('district')
        user_type = request.form.get('userType')
        language = request.form.get('language')

        if not age or not district or not user_type or not language:
            flash('Age, district, user type, and language are required.', 'error')
            return redirect(url_for('onboarding'))

        users_collection.update_one(
            {'_id': session['user_id']},
            {'$set': {'name': name, 'age': int(age), 'district': district, 'userType': user_type, 'language': language}}
        )
        if user_type == 'Pregnant Woman':
            return redirect(url_for('pregnancy_setup'))
        elif user_type == 'Mother':
            return redirect(url_for('mother_setup'))
        else:
            return redirect(url_for('caregiver_setup'))
    return render_template('onboarding.html')

@app.route('/mother_setup', methods=['GET', 'POST'])
@login_required
def mother_setup():
    if request.method == 'POST':
        data = {
            'email': session['email'],
            'childAge': request.form.get('childAge'),
            'numChildren': request.form.get('numChildren'),
            'trimester': request.form.get('trimester'),
            'lastDelivery': request.form.get('lastDelivery'),
            'antenatalVisits': request.form.get('antenatalVisits'),
            'vaccCard': request.form.get('vaccCard') == 'true',
            'created_at': datetime.utcnow()
        }
        if not data['childAge'] or not data['numChildren'] or not data['lastDelivery'] or not data['vaccCard']:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('mother_setup'))
        health_collection.insert_one(data)
        return redirect(url_for('health_assessment'))
    return render_template('mother_setup.html')

@app.route('/caregiver_setup', methods=['GET', 'POST'])
@login_required
def caregiver_setup():
    if request.method == 'POST':
        data = {
            'email': session['email'],
            'relation': request.form.get('relation'),
            'numDependents': request.form.get('numDependents'),
            'responsibilities': request.form.getlist('responsibilities'),
            'supportContact': request.form.get('supportContact'),
            'created_at': datetime.utcnow()
        }
        if not data['relation'] or not data['numDependents']:
            flash('Relation and Number of Dependents are required.', 'error')
            return redirect(url_for('caregiver_setup'))
        health_collection.insert_one(data)
        return redirect(url_for('health_assessment'))
    return render_template('caregiver_setup.html')

def send_email(to_email, subject, body):
    try:
        sender_email = EMAIL_USER
        password = EMAIL_PASS

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP server with a timeout and debug
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {to_email}: {e}")
        flash('Failed to send email notification to doctor/ASHA worker.', 'error')
    except Exception as e:
        logger.error(f"General error sending email to {to_email}: {e}")
        flash('Failed to send email notification to doctor/ASHA worker.', 'error')
        
@app.route('/pregnancy_health', methods=['GET', 'POST'])
@login_required
def pregnancy_health():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'msg': 'No data provided'}), 400

        # Fetch user's location from pregnancy_setup
        user_setup = health_collection.find_one({'email': session['email'], 'edd': {'$exists': True}}, sort=[('updated_at', -1)])
        location = user_setup.get('distance', 'N/A') if user_setup else 'N/A'

        form_data = {
            'email': session['email'],
            'lastCheckup': data.get('lastCheckup'),
            'antenatalVisits': data.get('antenatalVisits'),
            'mcpCard': data.get('mcpCard') == 'true',
            'ifaTaken': data.get('ifaTaken') == 'true',
            'ifaDays': data.get('ifaDays'),
            'dietDiversity': data.get('dietDiversity', []),
            'ageAtMarriage': data.get('ageAtMarriage'),
            'symptoms': data.get('symptoms', []),
            'deliveryLocation': data.get('deliveryLocation'),
            'chiranjeevi': data.get('chiranjeevi') == 'true',
            'created_at': datetime.now(timezone.utc)
        }
        health_collection.insert_one(form_data)

        # Send email if requested
        if data.get('sendEmail') == 'true':
            user_email = session['email']
            doctor_emails = ['vishwaschaudhary2672003@gmail.com', 'doctor2@gujhealth.gov.in']  # Replace with dynamic source
            subject = 'Pregnancy Health Update - Matru-Shishu Suraksha'
            body = f"""Pregnancy Health Update for {user_email}
            - Last Checkup: {form_data.get('lastCheckup', 'N/A')}
            - Antenatal Visits: {form_data.get('antenatalVisits', 'N/A')}
            - MCP Card: {form_data.get('mcpCard', 'N/A')}
            - IFA Taken: {form_data.get('ifaTaken', 'N/A')}
            - IFA Days: {form_data.get('ifaDays', 'N/A')}
            - Diet Diversity: {', '.join(form_data.get('dietDiversity', [])) or 'N/A'}
            - Age at Marriage: {form_data.get('ageAtMarriage', 'N/A')}
            - Symptoms: {', '.join(form_data.get('symptoms', [])) or 'N/A'}
            - Delivery Location: {form_data.get('deliveryLocation', 'N/A')}
            - Chiranjeevi Yojana: {form_data.get('chiranjeevi', 'N/A')}
            - Location: {location} km from health facility
            - Action Required: Review and contact the patient if needed."""

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = os.getenv('EMAIL_USER')
            recipients = [user_email] + doctor_emails
            msg['To'] = ', '.join(recipients)

            try:
                with smtplib.SMTP('smtp.gmail.com', 465) as server:  # Using SSL port 465
                    server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
                    server.send_message(msg)
                logger.info(f"Health update emailed to {recipients} for {user_email}")
            except Exception as e:
                logger.error(f"Email notification failed: {e}")
                flash('Failed to send email. Check your connection.', 'error')

        return jsonify({'msg': 'Data saved successfully.'}), 200

    return render_template('pregnancy_health.html')

@app.route('/child_health', methods=['GET', 'POST'])
@login_required
def child_health():
    if request.method == 'POST':
        data = {
            'email': session['email'],
            'vaccines': request.form.getlist('vaccines'),
            'lastVaccine': request.form.get('lastVaccine'),
            'vaccineSource': request.form.get('vaccineSource'),
            'bfStatus': request.form.get('bfStatus'),
            'bfInitiation': request.form.get('bfInitiation') == 'true',
            'foods': request.form.getlist('foods'),
            'vitaminA': request.form.get('vitaminA') == 'true',
            'illnesses': request.form.getlist('illnesses'),
            'weight': request.form.get('weight'),
            'height': request.form.get('height'),
            'malnutritionSigns': request.form.getlist('malnutritionSigns'),
            'anganwadiDistance': request.form.get('anganwadiDistance'),
            'healthWorker': request.form.get('healthWorker') == 'true',
            'created_at': datetime.utcnow(),
            'created_at': datetime.now(timezone.utc)
        }
        health_collection.insert_one(data)
        return redirect(url_for('health_assessment'))
    return render_template('child_health.html')

@app.route('/child_health_alert', methods=['POST'])
def send_child_health_alert():
    data = request.get_json()
    email = session.get('email')
    # Fetch the latest document inserted by the original route
    user_data = health_collection.find_one({'email': email}, sort=[('created_at', -1)])
    if not user_data:
        return jsonify({'msg': 'No data found for this user.'}), 400

    # Extract relevant fields, including location
    vaccination_schedule = user_data.get('vaccination_schedule', {'calendar_events': []})
    location = f"{user_data.get('anganwadiDistance', 'N/A')} km from Anganwadi"

    # Trigger alert if illnesses or malnutrition signs are reported
    if user_data.get('illnesses') or user_data.get('malnutritionSigns'):
        notify_health_worker(email, user_data, vaccination_schedule, location)
    return jsonify({'msg': 'Data saved successfully.'})

def notify_health_worker(email, data, vaccination_schedule, location):
    # Sample doctor emails (replace with a dynamic source like a MongoDB collection)
    doctor_emails = ['doctor1@gujhealth.gov.in', 'doctor2@gujhealth.gov.in']  # Add real doctor emails
    health_worker_email = 'asha@example.com'  # Replace with actual ASHA email or fetch dynamically

    illnesses = ', '.join(data.get('illnesses', [])) or 'no illnesses'
    malnutrition_signs = ', '.join(data.get('malnutritionSigns', [])) or 'no malnutrition signs'
    vaccines = ', '.join([event.get('title', 'No title') for event in vaccination_schedule.get('calendar_events', [])]) or 'No schedule available'

    message = f"""URGENT: Child Health Alert - Matru-Shishu Suraksha
    Emergency for child under {email}
    - Illnesses: {illnesses}
    - Malnutrition Signs: {malnutrition_signs}
    - Vaccination Schedule: {vaccines}
    - Location: {location}
    - Action Required: Immediate assessment recommended. Contact the family for details."""

    msg = MIMEText(message)
    msg['Subject'] = 'URGENT: Child Health Alert - Matru-Shishu Suraksha'
    msg['From'] = os.getenv('EMAIL_USER')
    recipients = [health_worker_email] + doctor_emails
    msg['To'] = ', '.join(recipients)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
            server.send_message(msg)
        logger.info(f"Alert emailed to {recipients} for {email}")
    except Exception as e:
        logger.error(f"Email notification failed: {e}")

@app.route('/api/health/history')
@login_required
def get_health_history():
    email = request.args.get('email')
    if not email:
        return jsonify({'msg': 'Email parameter is required.'}), 400

    # Query health records for the user
    history = list(health_collection.find({'email': email}).sort('created_at', -1))

    # Convert non-serializable types to JSON-compatible formats
    for record in history:
        if '_id' in record:
            record['_id'] = str(record['_id'])  # Convert ObjectId to string
        if 'created_at' in record and isinstance(record['created_at'], datetime):
            record['created_at'] = record['created_at'].isoformat()  # Convert datetime to ISO string
        # Handle other potential non-serializable fields if present
        if 'vaccination_schedule' in record and isinstance(record['vaccination_schedule'], dict):
            if 'calendar_events' in record['vaccination_schedule']:
                record['vaccination_schedule']['calendar_events'] = [
                    {k: str(v) if isinstance(v, ObjectId) else v for k, v in event.items()}
                    for event in record['vaccination_schedule']['calendar_events']
                ]

    return jsonify({'history': history})

@app.route('/api/community/tips', methods=['GET'])
def get_community_tips():
    # Simulated community tips (replace with a database or API call in production)
    tips = [
        "Regular weight checks help detect malnutrition early.",
        "Attend Anganwadi sessions for free nutrition support.",
        "Consult ASHA workers for vaccination reminders."
    ]
    return jsonify({'tips': tips})

@app.route('/health_assessment')
@login_required
def health_assessment():
    health_data = list(health_collection.find({'email': session['email']}))
    assessment = "Health Assessment: All parameters normal. Ensure regular checkups." if health_data else "No health data available."
    return render_template('health_assessment.html', assessment=assessment)

@app.route('/resources')
@login_required
def resources():
    return render_template('resources.html')

@app.route('/progress')
@login_required
def progress():
    health_data = list(health_collection.find({'email': session['email']}).sort('created_at', -1).limit(1))
    progress = "No progress data available" if not health_data else f"Antenatal Visits: {health_data[0].get('antenatalVisits', 0)}/4<br>IFA Taken: {health_data[0].get('ifaTaken', 'No')}"
    return render_template('progress.html', progress=progress)

@app.route('/dashboard')
@login_required
def dashboard():
    health_data = list(health_collection.find({'email': session['email']}).sort('created_at', -1).limit(1))
    progress = "No progress data available" if not health_data else f"Antenatal Visits: {health_data[0].get('antenatalVisits', 0)}/4<br>IFA Taken: {health_data[0].get('ifaTaken', 'No')}"
    user = health_collection.find_one({'email': session['email']})
    user_data = health_collection.find_one({'email': session['email']})
    notifications = user_data.get('notifications', []) if user_data else []
    return render_template('dashboard.html', notifications=notifications, progress=progress, GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    session.pop('role', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# API Routes
@app.route('/api/auth/language', methods=['GET'])
@login_required
def get_language():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        return jsonify({'error': 'Language not supported'}), 400

    return jsonify({'translations': translations[lang], 'language': lang}), 200

@app.route('/api/health/assess-malnutrition', methods=['POST'])
@login_required
def assess_malnutrition():
    try:
        data = request.get_json()
        age_months = float(data.get('age_months'))
        sex = data.get('sex')
        weight_kg = float(data.get('weight_kg'))
        height_cm = float(data.get('height_cm'))  # New field for height

        if not all([age_months, sex, weight_kg, height_cm]) or sex not in ['male', 'female']:
            return jsonify({'msg': 'Invalid input. Provide age_months, sex (male/female), weight_kg, and height_cm.'}), 400

        # Get WHO medians and SD for weight-for-age
        median_weight_age, sd_weight_age = get_median_weight(age_months, sex)
        z_score_weight_age = (weight_kg - median_weight_age) / sd_weight_age

        # Get WHO medians and SD for height-for-age
        median_height_age, sd_height_age = get_median_height(age_months, sex)
        z_score_height_age = (height_cm - median_height_age) / sd_height_age

        # Get WHO medians and SD for weight-for-height (approximated)
        median_weight_height, sd_weight_height = get_median_weight_for_height(height_cm, sex)
        z_score_weight_height = (weight_kg - median_weight_height) / sd_weight_height

        # Assess malnutrition status
        status_weight_age = 'Normal'
        if z_score_weight_age < -3:
            status_weight_age = 'Severe Underweight'
        elif z_score_weight_age < -2:
            status_weight_age = 'Moderate Underweight'

        status_height_age = 'Normal'
        if z_score_height_age < -3:
            status_height_age = 'Severe Stunting'
        elif z_score_height_age < -2:
            status_height_age = 'Moderate Stunting'

        status_weight_height = 'Normal'
        if z_score_weight_height < -3:
            status_weight_height = 'Severe Wasting'
        elif z_score_weight_height < -2:
            status_weight_height = 'Moderate Wasting'

        # Corrected function call with all five parameters
        diet_recommendation = get_diet_recommendation(age_months, sex, status_weight_age, status_weight_height, status_height_age)

        return jsonify({
            'msg': 'Malnutrition assessment completed.',
            'age_months': age_months,
            'sex': sex,
            'weight_kg': weight_kg,
            'height_cm': height_cm,
            'median_weight_age': round(median_weight_age, 2),
            'median_height_age': round(median_height_age, 2),
            'median_weight_height': round(median_weight_height, 2),
            'z_score_weight_age': round(z_score_weight_age, 2),
            'z_score_height_age': round(z_score_height_age, 2),
            'z_score_weight_height': round(z_score_weight_height, 2),
            'status_weight_age': status_weight_age,
            'status_height_age': status_height_age,
            'status_weight_height': status_weight_height,
            'diet_recommendation': diet_recommendation,
            'recommendation': 'Consult a health worker for abnormal results.'
        }), 200
    except Exception as e:
        logger.error(f"Error assessing malnutrition: {e}")
        return jsonify({'msg': 'Error assessing malnutrition.', 'error': str(e)}), 500

def get_median_weight(age_months, sex):
    who_male_medians = {0: 3.3, 1: 4.0, 2: 4.7, 3: 5.4, 4: 6.1, 5: 6.7, 6: 7.3, 7: 7.8, 8: 8.3, 9: 8.7,
                        10: 9.1, 11: 9.5, 12: 9.8, 24: 11.8, 36: 13.8, 48: 15.7, 60: 17.0}
    who_female_medians = {0: 3.2, 1: 3.9, 2: 4.6, 3: 5.2, 4: 5.9, 5: 6.5, 6: 7.0, 7: 7.5, 8: 8.0, 9: 8.4,
                          10: 8.8, 11: 9.2, 12: 9.5, 24: 11.3, 36: 13.3, 48: 15.2, 60: 16.5}
    who_sd_weight = 1.0

    ref = who_male_medians if sex == 'male' else who_female_medians
    ages = sorted(ref.keys())
    if age_months <= ages[0]:
        return ref[ages[0]], who_sd_weight
    if age_months >= ages[-1]:
        return ref[ages[-1]], who_sd_weight
    for i in range(len(ages)-1):
        if ages[i] <= age_months <= ages[i+1]:
            median = ref[ages[i]] + (ref[ages[i+1]] - ref[ages[i]]) * (age_months - ages[i]) / (ages[i+1] - ages[i])
            return median, who_sd_weight
    return 10.0, who_sd_weight

def get_median_height(age_months, sex):
    who_male_heights = {0: 49.9, 1: 54.7, 2: 58.4, 3: 61.4, 4: 63.9, 5: 66.0, 6: 67.6, 7: 69.2, 8: 70.6, 9: 71.9,
                        10: 73.1, 11: 74.1, 12: 75.0, 24: 87.1, 36: 95.8, 48: 103.3, 60: 109.2}
    who_female_heights = {0: 49.1, 1: 53.7, 2: 57.1, 3: 60.0, 4: 62.4, 5: 64.5, 6: 66.1, 7: 67.6, 8: 68.9, 9: 70.1,
                          10: 71.3, 11: 72.3, 12: 73.2, 24: 85.4, 36: 94.0, 48: 101.4, 60: 107.4}
    who_sd_height = 2.0

    ref = who_male_heights if sex == 'male' else who_female_heights
    ages = sorted(ref.keys())
    if age_months <= ages[0]:
        return ref[ages[0]], who_sd_height
    if age_months >= ages[-1]:
        return ref[ages[-1]], who_sd_height
    for i in range(len(ages)-1):
        if ages[i] <= age_months <= ages[i+1]:
            median = ref[ages[i]] + (ref[ages[i+1]] - ref[ages[i]]) * (age_months - ages[i]) / (ages[i+1] - ages[i])
            return median, who_sd_height
    return 100.0, who_sd_height

def get_median_weight_for_height(height_cm, sex):
    # Simplified approximation based on WHO weight-for-height charts
    who_male_weight_height = {65: 7.2, 80: 10.4, 100: 15.0}
    who_female_weight_height = {65: 7.0, 80: 10.1, 100: 14.7}
    who_sd_weight_height = 0.8

    ref = who_male_weight_height if sex == 'male' else who_female_weight_height
    heights = sorted(ref.keys())
    if height_cm <= heights[0]:
        return ref[heights[0]], who_sd_weight_height
    if height_cm >= heights[-1]:
        return ref[heights[-1]], who_sd_weight_height
    for i in range(len(heights)-1):
        if heights[i] <= height_cm <= heights[i+1]:
            median = ref[heights[i]] + (ref[heights[i+1]] - ref[heights[i]]) * (height_cm - heights[i]) / (heights[i+1] - heights[i])
            return median, who_sd_weight_height
    return 15.0, who_sd_weight_height

def get_diet_recommendation(age_months, sex, status_weight_age, status_weight_height, status_height_age):
    base_diet = "For a healthy child, include breast milk (if under 2), fruits like bananas or mangoes, vegetables like spinach or carrots, grains like rice or roti, and proteins like lentils or eggs daily. Offer small, frequent meals and consult a health worker."
    
    if age_months <= 24 and 'Severe' in status_weight_age or 'Severe' in status_weight_height or 'Severe' in status_height_age:
        return "URGENT: Severe malnutrition detected. For a child under 2, continue breastfeeding and give small, frequent meals of energy-rich foods like peanut paste or mashed potatoes with milk. Add vitamin A-rich foods (e.g., sweet potato) and zinc (e.g., pumpkin seeds). Seek medical help immediately. " + base_diet
    elif age_months <= 24 and 'Moderate' in status_weight_age or 'Moderate' in status_weight_height or 'Moderate' in status_height_age:
        return "Moderate malnutrition detected. For a child under 2, boost breastfeeding and add nutrient-rich foods like mashed dal, yogurt, and boiled vegetables. Include a daily fruit like papaya. " + base_diet
    elif age_months > 24 and 'Severe' in status_weight_age or 'Severe' in status_weight_height or 'Severe' in status_height_age:
        return "URGENT: Severe malnutrition detected. For a child over 2, offer 5-6 small meals daily with energy-dense foods like khichdi with ghee, milk with nuts, and fortified porridge. Add vitamin A (e.g., carrots) and zinc (e.g., chickpeas). Seek medical help now. " + base_diet
    elif age_months > 24 and 'Moderate' in status_weight_age or 'Moderate' in status_weight_height or 'Moderate' in status_height_age:
        return "Moderate malnutrition detected. For a child over 2, increase intake with meals like roti with dal, rice with vegetables, and a glass of milk. Add fruits like guava and nuts if possible. " + base_diet
    return base_diet

@app.route('/api/health/submit-edd', methods=['POST'])
@login_required
def submit_edd():
    try:
        data = request.get_json()
        edd = data.get('edd')
        if not edd or not datetime.strptime(edd, '%Y-%m-%d'):
            return jsonify({'msg': 'Invalid date format. Use YYYY-MM-DD.'}), 400

        schedule = generate_vaccination_schedule(edd)
        health_collection.update_one(
            {'email': session['email']},
            {'$set': {'edd': edd, 'vaccination_schedule': schedule}},
            upsert=True
        )
        notify_vaccination_schedule(session['email'], schedule)  # Local notification
        logger.info(f"Vaccination schedule generated for {session['email']}: {schedule}")
        return jsonify({
            'msg': 'EDD and vaccination schedule updated successfully.',
            'edd': edd,
            'vaccination_schedule': schedule
        }), 200
    except Exception as e:
        logger.error(f"Error updating EDD: {e}")
        return jsonify({'msg': 'Error updating EDD.', 'error': str(e)}), 500

@app.route('/api/health/district')
@login_required
def get_district():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            for component in data['results'][0]['address_components']:
                if 'administrative_area_level_2' in component['types']:
                    return jsonify({'district': component['long_name']})
    return jsonify({'district': 'Unknown district'})

@app.route('/api/health/facilities')
def get_facilities():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    try:
        lat, lon = float(lat), float(lon)
        facilities = get_nearby_facilities(lat, lon)
        return jsonify({'facilities': facilities})
    except ValueError as e:
        return jsonify({'error': 'Invalid latitude or longitude'}), 400

@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        message = data['message']
        user_data = health_collection.find_one({'email': session['email']})
        context = f"Trimester: {user_data.get('trimester', 'unknown')}, Health Access: {user_data.get('healthAccess', 'unknown')}, Previous Pregnancies: {user_data.get('prevPregnancies', '0')}"

        # Check if message is a health-related question
        health_keywords = ['eat', 'vaccine', 'health', 'nutrition', 'pregnancy', 'child']
        is_health_query = any(keyword in message.lower() for keyword in health_keywords)

        response = "Sorry, I couldn’t process that. Please try again or consult a healthcare worker."

        if is_health_query:
            response = get_conversational_response(message, context)

        return jsonify({'response': response})
    return render_template('dashboard.html')  # Updated to use dashboard.html with chatbot

# @app.route('/api/chatbot/query', methods=['POST'])
# def chatbot_query():
#     logger.info(f"Received chatbot query: {request.get_json()}")
#     data = request.get_json()
#     if not data or 'message' not in data:
#         logger.error("No message provided in request")
#         return jsonify({'error': 'No message provided'}), 400

#     message = data['message'].lower().strip()
#     user_data = health_collection.find_one({'email': session.get('email', 'unknown')})
#     context = f"Trimester: {user_data.get('trimester', 'unknown')}, Health Access: {user_data.get('healthAccess', 'unknown')}, Previous Pregnancies: {user_data.get('prevPregnancies', '0')}"

#     # Try conversational model
#     response = get_conversational_response(message, context)
#     logger.info(f"Conversational Response for '{message}': {response}")
#     if response and response.lower() != "no response generated." and response.strip():
#         return jsonify({'response': response})

#     # Fall back to HEALTH_RESPONSES if keyword matches
#     for key, value in HEALTH_RESPONSES.items():
#         if key in message:
#             return jsonify({'response': value['primary']})

#     # Fall back to Gemini API if available
#     if gemini_model:
#         try:
#             prompt = f"Provide maternal or child health advice based on the following context: {context}. Question: {message}. Answer in a concise, supportive tone, referencing India’s health guidelines where applicable."
#             gemini_response = gemini_model.generate_content(prompt, stream=False)
#             response = gemini_response.text if gemini_response else "No response from Gemini. Please try again."
#             logger.info(f"Gemini Response for '{message}': {response}")
#             return jsonify({'response': response})
#         except Exception as e:
#             logger.error(f"Gemini API error: {e}")
#             return jsonify({'error': 'Error processing request. Consult a healthcare worker.'})
#     else:
#         return jsonify({'error': 'Sorry, I couldn’t find an answer. Please consult a healthcare worker.'})
@app.route('/api/chatbot/query', methods=['POST'])
@login_required  # Added back if authentication is required
def chatbot_query():
    logger.info(f"Received chatbot query: {request.get_json()}")
    data = request.get_json()
    if not data or 'message' not in data:
        logger.error("No message provided in request")
        return jsonify({'error': 'No message provided'}), 400

    message = data['message'].lower().strip()
    user_data = health_collection.find_one({'email': session.get('email', 'unknown')})
    context = f"Trimester: {user_data.get('trimester', 'unknown')}, Health Access: {user_data.get('healthAccess', 'unknown')}, Previous Pregnancies: {user_data.get('prevPregnancies', '0')}"

    # Use Gemini API for all responses
    if gemini_model:
        try:
            prompt = f"Provide maternal or child health advice based on the following context: {context}. Question: {message}. Answer in a concise, supportive tone, referencing India’s health guidelines where applicable."
            gemini_response = gemini_model.generate_content(prompt, stream=False)
            response = gemini_response.text if gemini_response and hasattr(gemini_response, 'text') else "No response from Gemini."
            logger.info(f"Gemini Response for '{message}': {response}")  # Log for debugging, not print
            return jsonify({'response': response})
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return jsonify({'error': 'Error processing request. Consult a healthcare worker.'})
    else:
        return jsonify({'error': 'Gemini model unavailable. Please try again later.'})

def get_nearby_facilities(lat, lon):
    try:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=100000&type=clinic|hospital|lodging|point_of_interest&key={GOOGLE_MAPS_API_KEY}"
        logger.info(f"Fetching facilities from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Google Maps API response: {data}")  # Log full response
        facilities = data.get('results', [])
        if not facilities:
            logger.warning(f"No facilities found within 100 km of {lat}, {lon}")
        return [{
            'name': f['name'],
            'lat': f['geometry']['location']['lat'],
            'lon': f['geometry']['location']['lng'],
            'distance': calculate_distance(lat, lon, f['geometry']['location']['lat'], f['geometry']['location']['lng']),
            'directions_url': f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={f['geometry']['location']['lat']},{f['geometry']['location']['lng']}&travelmode=driving"
        } for f in facilities if f['types'] and any(t in ['clinic', 'hospital'] for t in f['types'])]
    except requests.exceptions.RequestException as e:
        logger.error(f"Google Maps API error: {e}")
        return []

@app.route('/api/health/feedback', methods=['POST'])
@login_required
def save_feedback():
    try:
        data = request.get_json()
        score = data.get('score')
        if not score or not 1 <= int(score) <= 5:
            return jsonify({'msg': 'Valid score (1-5) is required.'}), 400

        feedback = {
            'email': session['email'],
            'score': int(score),
            'created_at': datetime.utcnow()
        }
        feedback_collection.insert_one(feedback)
        return jsonify({'msg': 'Feedback submitted successfully.'}), 201
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({'msg': 'Server error.', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 3000)))