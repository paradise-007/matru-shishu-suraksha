Matru-Shishu Suraksha Dashboard
Overview
Matru-Shishu Suraksha is a web application designed to support maternal and child healthcare by providing users with tools to locate nearby medical facilities and interact with a chatbot, MamaBot, for health-related queries. The dashboard offers a user-friendly interface with features like geolocation-based facility search and real-time chatbot responses.
Features

Find Nearby Facilities: Locate medical facilities within a 100 km radius using geolocation and display them on a Google Maps interface.
MamaBot Chatbot: Ask health-related questions (e.g., "What should I eat in my 2nd trimester?") and receive responses from MamaBot. Supports text input (with Enter key submission) and voice input.
Responsive Design: Built with Tailwind CSS for a modern, responsive layout that works across devices.
User Authentication: Displays the logged-in user's email and provides a logout option.
Interactive Map: Visualizes nearby facilities with markers using the Google Maps API.

Technologies Used

Frontend: HTML, Jinja2 (Flask templating), Tailwind CSS, JavaScript
Backend: Flask (Python) for API endpoints (/api/chatbot/query, /api/health/facilities)
APIs: Google Maps API for facility mapping
Libraries: Fetch API for asynchronous requests, Navigator Geolocation API

Setup Instructions
Prerequisites

Python 3.8+
Flask (pip install flask)
A Google Maps API key
A web server with session management for authentication

Installation

Clone the Repository:
git clone https://github.com/yourusername/matru-shishu-suraksha.git
cd matru-shishu-suraksha


Install Dependencies:
pip install -r requirements.txt


Set Up Environment Variables:Create a .env file in the project root and add your Google Maps API key:
GOOGLE_MAPS_API_KEY=your_api_key_here


Run the Application:
python app.py

The application will be available at http://localhost:5000.


Project Structure---////as per the git hub repositry
matru-shishu-suraksha/
├── app.py                   # Flask application
├── templates/
│   ├── base.html            # Base template
│   ├── dashboard.html       # Dashboard template with chatbot and map
├── static/
│   ├── css/                 # Tailwind CSS or custom styles
│   ├── js/                  # Custom JavaScript (if separate)
├── requirements.txt         # Python dependencies
└── README.md                # This file

Usage

Log In: Access the dashboard via the login page. The dashboard displays the user's email or "Guest" if not logged in.
Find Facilities:
Click the "Find Nearby Facilities" button to fetch and display medical facilities based on your geolocation.
View facilities on an interactive Google Map with clickable markers.


Ask MamaBot:
Type a question in the textarea and press Enter or click "Send" to get a response.
Use the voice input button for speech-to-text queries (if supported by the browser).
Click "Hear Response" to listen to MamaBot's response (if text-to-speech is implemented).


Logout: Click the "Logout" link to end the session.

API Endpoints

POST /api/chatbot/query: Sends a user query to MamaBot and returns a response.
Request: { "message": "user question" }
Response: { "response": "MamaBot answer" } or { "error": "error message" }


GET /api/health/facilities?lat=&lon=: Retrieves nearby medical facilities.
Response: { "facilities": [{ "name": "Facility Name", "lat": 12.34, "lon": 56.78, "distance": 10.5, "directions_url": "url" }, ...] }

