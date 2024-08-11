from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGODB_URI = "mongodb+srv://mailonlyforbusinesses:uh6aNXmSBd5HkEGX@cluster0.tctw0mf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGODB_URI)
db = client.get_database("eventsdb")
events_collection = db.events
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Events Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        form {
            margin-top: 20px;
        }
        input, button {
            margin: 5px 0;
            padding: 5px;
        }
        .delete-btn {
            background-color: #ff4d4d;
            color: white;
            border: none;
            padding: 5px 10px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Company Events Tracker</h1>
    
    <h2>Add New Event</h2>
    <form id="addEventForm">
        <input type="date" id="eventDate" required>
        <input type="text" id="companyName" placeholder="Company Name" required>
        <input type="text" id="eventType" placeholder="Event Type" required>
        <button type="submit">Add Event</button>
    </form>

    <h2>Upcoming Events</h2>
    <table id="eventsTable">
        <thead>
            <tr>
                <th>Date</th>
                <th>Company</th>
                <th>Event Type</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody id="eventsTableBody"></tbody>
    </table>

    <script>
        const API_URL = '';

        async function addEvent(event) {
            try {
                const response = await fetch(`${API_URL}/api/events`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(event),
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Failed to add event');
                }
                refreshEvents();
            } catch (error) {
                console.error('Error adding event:', error);
                alert(error.message);
            }
        }

        async function getEvents() {
            try {
                const response = await fetch(`${API_URL}/api/events`);
                if (!response.ok) {
                    throw new Error('Failed to fetch events');
                }
                return await response.json();
            } catch (error) {
                console.error('Error getting events:', error);
                return [];
            }
        }

        async function deleteEvent(id) {
            if (!confirm('Are you sure you want to delete this event?')) {
                return;
            }
            try {
                const response = await fetch(`${API_URL}/api/events/${id}`, {
                    method: 'DELETE',
                });
                if (!response.ok) {
                    throw new Error('Failed to delete event');
                }
                refreshEvents();
            } catch (error) {
                console.error('Error deleting event:', error);
                alert('Failed to delete event');
            }
        }

        async function refreshEvents() {
            const events = await getEvents();
            const tableBody = document.getElementById('eventsTableBody');
            tableBody.innerHTML = '';

            events.forEach(event => {
                const row = tableBody.insertRow();
                row.insertCell().textContent = new Date(event.date).toLocaleDateString();
                row.insertCell().textContent = event.company;
                row.insertCell().textContent = event.type;
                const actionCell = row.insertCell();
                const deleteButton = document.createElement('button');
                deleteButton.textContent = 'Delete';
                deleteButton.className = 'delete-btn';
                deleteButton.onclick = () => deleteEvent(event._id);
                actionCell.appendChild(deleteButton);
            });
        }

        document.getElementById('addEventForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const eventDate = new Date(document.getElementById('eventDate').value);
            const currentDate = new Date();
            currentDate.setHours(0, 0, 0, 0);

            if (eventDate < currentDate) {
                alert('Cannot add events for past dates');
                return;
            }

            const event = {
                date: eventDate.toISOString(),
                company: document.getElementById('companyName').value,
                type: document.getElementById('eventType').value
            };
            await addEvent(event);
            e.target.reset();
        });

        refreshEvents();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/events', methods=['GET'])
def get_events():
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events = list(events_collection.find({"date": {"$gte": current_date}}).sort("date", 1))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify(events)

@app.route('/api/events', methods=['POST'])
def add_event():
    event_data = request.json
    event_date = datetime.fromisoformat(event_data['date'].replace('Z', '')).replace(tzinfo=None)
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if event_date < current_date:
        return jsonify({"message": "Cannot add events for past dates"}), 400

    new_event = {
        "date": event_date,
        "company": event_data['company'],
        "type": event_data['type']
    }
    result = events_collection.insert_one(new_event)
    new_event['_id'] = str(result.inserted_id)
    return jsonify(new_event), 201

@app.route('/api/events/<string:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        result = events_collection.delete_one({"_id": ObjectId(event_id)})
        if result.deleted_count == 0:
            return jsonify({"message": "Event not found"}), 404
        return jsonify({"message": "Event deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error deleting event: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 8080)))