const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bodyParser = require('body-parser');
const moment = require('moment-timezone');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

const MONGODB_URI = "mongodb+srv://mailonlyforbusinesses:uh6aNXmSBd5HkEGX@cluster0.tctw0mf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0";

mongoose.connect(MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log("Connected to MongoDB Atlas"))
.catch(err => console.error("Error connecting to MongoDB:", err));

// Event model
const EventSchema = new mongoose.Schema({
  date: Date,
  company: String,
  type: String
});

const Event = mongoose.model('Event', EventSchema);

// Helper function to get the start of day in IST
function getStartOfDayIST(date) {
  return moment(date).tz('Asia/Kolkata').startOf('day').toDate();
}

// Routes
app.get('/api/events', async (req, res) => {
  try {
    const currentDate = getStartOfDayIST(new Date());
    const events = await Event.find({ date: { $gte: currentDate } }).sort({ date: 1 });
    res.json(events);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching events', error: error.message });
  }
});

app.post('/api/events', async (req, res) => {
  try {
    const { date, company, type } = req.body;
    const eventDate = getStartOfDayIST(date);
    const currentDate = getStartOfDayIST(new Date());

    if (eventDate < currentDate) {
      return res.status(400).json({ message: 'Cannot add events for past dates' });
    }

    const newEvent = new Event({ date: eventDate, company, type });
    await newEvent.save();
    res.status(201).json(newEvent);
  } catch (error) {
    res.status(400).json({ message: 'Error creating event', error: error.message });
  }
});

app.put('/api/events/:id', async (req, res) => {
  try {
    const { date, company, type } = req.body;
    const eventDate = getStartOfDayIST(date);
    const currentDate = getStartOfDayIST(new Date());

    if (eventDate < currentDate) {
      return res.status(400).json({ message: 'Cannot update events to past dates' });
    }

    const updatedEvent = await Event.findByIdAndUpdate(
      req.params.id,
      { date: eventDate, company, type },
      { new: true }
    );

    if (!updatedEvent) {
      return res.status(404).json({ message: 'Event not found' });
    }

    res.json(updatedEvent);
  } catch (error) {
    res.status(400).json({ message: 'Error updating event', error: error.message });
  }
});

app.delete('/api/events/:id', async (req, res) => {
  try {
    const event = await Event.findByIdAndDelete(req.params.id);
    if (!event) {
      return res.status(404).json({ message: 'Event not found' });
    }
    res.json({ message: 'Event deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Error deleting event', error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});