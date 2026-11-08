
# AI Film Studio for Students

AI Film Studio for Students is a full-stack web application
that helps students transform educational topics into
short, narrated videos using artificial intelligence.

## Project Overview

The application combines AI-generated educational scripts,
editable storyboards, text-based scene visuals, AI narration,
and automated video assembly.

Students can create and download an MP4 video directly
from the website.

## Current Features

- Generate educational scripts from a topic
- Select an audience, video length, and presentation style
- Generate a structured storyboard
- Edit storyboard scenes and narration
- Save, load, import, and export storyboards
- Generate AI narration for each scene
- Create text-based visuals for storyboard scenes
- Combine scenes and narration into an MP4 video
- Preview the completed video in the browser
- Download the finished MP4

## Project Goal

My goal is to combine my interests in filmmaking,
storytelling, education, and software engineering
by building a practical AI-powered creative tool.

## Why This Project Matters

Creating educational videos normally requires writing,
storyboarding, recording narration, editing, and exporting.

AI Film Studio brings these steps together in one application,
helping students experiment with educational storytelling
and video production.

## Technology Stack

### Frontend
- React
- JavaScript
- Vite

### Backend
- Python
- FastAPI
- OpenAI API

### Video Production
- OpenAI text-to-speech
- Pillow for scene images
- FFmpeg for video rendering and assembly

### Development
- Visual Studio Code
- Git and GitHub
- Windows Subsystem for Linux (WSL)

## 10-Week Roadmap

### Week 1: Foundation
Set up GitHub, development tools, React frontend, and FastAPI backend.

### Week 2: Script Generator
Allow users to enter a topic and generate an educational script.

### Week 3: Storyboard
Turn the script into scenes.

### Week 4: Voice-over
Generate narration audio.

### Week 5: Visuals
Generate or select visuals for each scene.

### Week 6: Captions
Create subtitles and caption timing.

### Week 7: Video Assembly
Combine visuals, narration, and captions into a video.

### Week 8: Editing Tools
Allow users to edit, reorder, add, and delete scenes.

### Week 9: Polish and Portfolio
Improve UI, documentation, and demo videos.

### Week 10: Launch
Deploy the app, test with users, and prepare the final portfolio.

## Final Deliverables

- Working web application
- GitHub repository
- Live demo
- Sample educational videos
- Technical documentation
- Portfolio page
- Resume-ready project description

## Author

Built by Nikolay Prokofiev as a summer AI portfolio project.

## Week 1 Reflection

During Week 1, I built the foundation for AI Film Studio for Students.

### What I completed

- Created a GitHub repository for the project
- Wrote the project mission and roadmap
- Installed Python, Node.js, VS Code, and Git
- Created a React frontend with Vite
- Built the first homepage
- Added a topic input form
- Created a FastAPI backend
- Added a health check endpoint
- Moved the backend into the correct project structure
- Connected the React frontend to the FastAPI backend

### What I learned

- How a full-stack web application is organized
- How React is used to build the user interface
- How React state stores user input
- How a form sends information from the browser
- How FastAPI creates backend API endpoints
- How the frontend communicates with the backend using `fetch`
- How CORS allows the frontend and backend to communicate
- How Git and GitHub track project progress
- How to troubleshoot folder, terminal, and virtual environment issues


## Week 2 — AI Script Generator (Days 8–14)

### What I Built

During Week 2, I connected my AI Film Studio application to the OpenAI API and created a working AI script generator.

The application now allows users to:

- Enter an educational video topic.
- Select an audience: Elementary School, Middle School, High School, or College.
- Choose a video length: 30, 60, or 90 seconds.
- Select a presentation style: Educational, Fun, Documentary, or Storytelling.
- Generate a structured AI script with a title, introduction, three scenes, and conclusion.
- View narration and visual instructions for each section.

### Technologies Used

- Python and FastAPI for the backend
- React and JavaScript for the frontend
- OpenAI API with GPT-6 Luna for script generation
- JSON for structured data
- Git and GitHub for version control

### Testing

I tested the application using five different educational topics: the fall of the Roman Empire, photosynthesis, inflation, vaccines, and how AI learns from data.

All five tests generated correctly structured scripts, and the audience, length, and style settings influenced the results.

### What I Learned

I learned how a frontend communicates with a backend, how to send information to an AI model through an API, and how to turn an AI-generated response into structured JSON that can be displayed on a website.

I also learned that AI-generated content needs testing for accuracy, consistency, and appropriate length.

### Next Steps

During Week 3, I plan to build a storyboard generator that turns the AI script into a sequence of scenes for video production.

### Current working demo

A user can type an educational topic into the React web app.

The frontend sends that topic to the FastAPI backend.

The backend returns a simple video plan.

The frontend displays the video plan on the page.

Example topic:

```text
How volcanoes erupt
```


## Running the Application Locally

### Requirements

Install the following software:

- Python 3
- Node.js and npm
- FFmpeg
- Git

An OpenAI API key with access to text generation and
text-to-speech is also required.

### 1. Clone the Repository

```bash
git clone https://github.com/SharpBecarre/ai-film-studio-for-students.git
cd ai-film-studio-for-students
```


### 2. Set Up the Backend

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-dotenv openai pillow
```

Create a file named `.env` in the `backend` directory:

```text
OPENAI_API_KEY=your_api_key_here
```

Never commit this file or share your API key.

### 3. Start the Backend

From the project root, with the virtual environment active:

```bash
uvicorn main:app --app-dir backend --reload
```

The API will be available at:

http://localhost:8000

### 4. Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local address displayed by Vite, usually:

http://localhost:5173

### 5. Create a Video

1. Enter an educational topic.
2. Choose the audience, length, and presentation style.
3. Generate an AI script.
4. Generate a storyboard.
5. Edit the storyboard if needed.
6. Click Generate Video.
7. Preview the completed video.
8. Download the MP4.

### Notes

- The application currently runs locally.
- Video generation requires an internet connection and
  uses OpenAI API credits.
- Current scene visuals are text-based slides.
- AI-generated cinematic imagery and synchronized captions
  are potential future improvements.
