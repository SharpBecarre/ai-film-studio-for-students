# AI Film Studio for Students

AI Film Studio for Students is a web application that helps students turn any educational topic into a short video.

The app will use AI to generate:

- a short educational script
- a storyboard
- narration / voice-over
- visuals for each scene
- captions
- a final exportable video

## Project Goal

The goal of this project is to build a full-stack AI application that combines software engineering, artificial intelligence, education, and media production.

## Why This Project Matters

Many students understand topics better when they see them explained visually. This tool will help students quickly create educational videos for studying, presentations, and class projects.

## Planned Technology Stack

- React for the frontend
- Python and FastAPI for the backend
- OpenAI API for script generation and AI features
- FFmpeg or MoviePy for video assembly
- GitHub for version control

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

### Current working demo

A user can type an educational topic into the React web app.

The frontend sends that topic to the FastAPI backend.

The backend returns a simple video plan.

The frontend displays the video plan on the page.

Example topic:

```text
How volcanoes erupt

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