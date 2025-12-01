# Voice Assistant

A Python-based voice assistant that responds to wake words and can handle reminders, weather queries, and news updates. The assistant uses speech recognition for voice input and text-to-speech for responses.

## Features

- **Wake Word Activation**: Responds to wake phrases like "Hey Assistant", "OK Assistant", or "Assistant"
- **Reminder Management**: Set reminders with natural language time expressions (e.g., "remind me to take medicine in 10 minutes")
- **Weather Information**: Get current weather updates for any city using OpenWeatherMap API
- **News Headlines**: Read top news headlines from NewsAPI or BBC RSS feed
- **Persistent Reminders**: Reminders are stored in SQLite database and persist across restarts
- **Background Scheduling**: Uses APScheduler to manage reminder notifications

## Requirements

- Python 3.7 or higher
- Microphone for voice input
- Audio output device for text-to-speech
- Internet connection (for weather, news, and speech recognition)

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd VoiceAssistant
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: On some systems, you may need to install `portaudio` separately:
   - **Ubuntu/Debian**: `sudo apt-get install portaudio19-dev`
   - **macOS**: `brew install portaudio`
   - **Windows**: Usually included with PyAudio installation

## Configuration

Create a `.env` file in the project root directory to configure API keys (optional):

```env
OWM_API_KEY=your_openweathermap_api_key
NEWSAPI_KEY=your_newsapi_key
```

### Getting API Keys

- **OpenWeatherMap API Key** (optional, for weather):
  1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
  2. Get your free API key
  3. Add it to `.env` as `OWM_API_KEY`

- **NewsAPI Key** (optional, for news):
  1. Sign up at [NewsAPI](https://newsapi.org/)
  2. Get your free API key
  3. Add it to `.env` as `NEWSAPI_KEY`

**Note**: The assistant will work without these API keys, but weather and news features will be limited. News will fall back to BBC RSS feed if NewsAPI key is not provided.

## Usage

1. **Activate the virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate
   ```

2. **Run the assistant:**
   ```bash
   python assistant.py
   ```

3. **Interact with the assistant:**
   - Say one of the wake words: "Hey Assistant", "OK Assistant", or "Assistant"
   - Wait for the "Yes?" response
   - Give your command

### Example Commands

- **Set a reminder:**
  - "Set a reminder to take medicine in 10 minutes"
  - "Remind me to call John at 3 PM"
  - "Remind me to water plants in 2 hours"

- **Check weather:**
  - "What's the weather in London?"
  - "Weather in New York"
  - "Weather" (will prompt for city)

- **Read news:**
  - "Read the news"
  - "What are the headlines?"

- **Get help:**
  - "Help"

- **Exit:**
  - "Exit", "Quit", or "Stop"

## Project Structure

```
VoiceAssistant/
├── assistant.py          # Main application file
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .env                 # Environment variables (create this)
└── assistant_reminders.db  # SQLite database (created automatically)
```

## Dependencies

- **SpeechRecognition** (3.8.1): Speech-to-text conversion using Google Speech Recognition
- **pyttsx3** (2.90): Text-to-speech engine
- **requests** (2.31.0): HTTP library for API calls
- **APScheduler** (3.10.1): Background task scheduling for reminders
- **pyaudio** (0.2.13): Audio I/O library for microphone input
- **python-dotenv** (1.0.1): Environment variable management

## How It Works

1. **Wake Word Detection**: The assistant continuously listens for wake words
2. **Command Processing**: After activation, it listens for your command
3. **Natural Language Parsing**: Commands are parsed to extract intent and parameters
4. **Task Execution**: The assistant performs the requested action (reminder, weather, news)
5. **Reminder Scheduling**: Reminders are stored in SQLite and scheduled using APScheduler
6. **Persistent Storage**: Reminders persist across application restarts

## Troubleshooting

### Microphone Issues
- Ensure your microphone is connected and working
- Check system audio permissions
- Try adjusting microphone sensitivity in system settings

### Speech Recognition Errors
- Ensure you have an active internet connection (uses Google Speech Recognition)
- Speak clearly and reduce background noise
- Check microphone input levels

### Audio Output Issues
- Verify your system's audio output is working
- On Linux, you may need to install additional TTS engines:
  ```bash
  sudo apt-get install espeak
  ```

### API Errors
- Verify your API keys are correct in the `.env` file
- Check your internet connection
- Ensure API quotas haven't been exceeded

## License

This project is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.