import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [videoPlan, setVideoPlan] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!topic.trim()) {
      alert("Please enter a topic.");
      return;
    }

    setLoading(true);
    setVideoPlan(null);

    try {
      const response = await fetch("http://localhost:8000/video-plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ topic: topic }),
      });

      const data = await response.json();
      setVideoPlan(data);
    } catch (error) {
      alert("Could not connect to backend API.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: "40px", fontFamily: "Arial", maxWidth: "700px" }}>
      <h1>AI Film Studio for Students</h1>

      <p>Turn any educational topic into a short narrated video using AI.</p>

      <form onSubmit={handleSubmit}>
        <label htmlFor="topic">
          <strong>Enter your video topic:</strong>
        </label>

        <br />

        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          placeholder="Example: How volcanoes erupt"
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "10px",
            fontSize: "16px",
          }}
        />

        <br />

        <button
          type="submit"
          style={{
            marginTop: "15px",
            padding: "12px 20px",
            fontSize: "16px",
            cursor: "pointer",
          }}
        >
          {loading ? "Generating..." : "Generate Video Plan"}
        </button>
      </form>

      {videoPlan && (
        <section style={{ marginTop: "30px" }}>
          <h2>{videoPlan.title}</h2>

          <p>
            <strong>Topic:</strong> {videoPlan.topic}
          </p>

          <h3>Planned Steps</h3>

          <ol>
            {videoPlan.steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </section>
      )}
    </main>
  );
}

export default App;