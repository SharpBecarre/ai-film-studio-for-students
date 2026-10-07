import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("High School");
  const [videoLength, setVideoLength] = useState("60");
  const [style, setStyle] = useState("Educational");
  const [script, setScript] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!topic.trim()) {
      alert("Please enter a topic.");
      return;
    }

    setLoading(true);
    setScript("");

    try {
      const response = await fetch("http://localhost:8000/generate-script", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: topic,
          audience: audience,
          video_length: videoLength,
          style: style,
        }),
      });

      const data = await response.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      setScript(data.script);
    } catch (error) {
      alert("Could not connect to the AI Film Studio backend.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        padding: "40px",
        fontFamily: "Arial",
        maxWidth: "800px",
        margin: "0 auto",
      }}
    >
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
            boxSizing: "border-box",
          }}
        />
        <div style={{ marginTop: "20px" }}>
          <label htmlFor="audience">
            <strong>Audience:</strong>
          </label>

          <br />

          <select
            id="audience"
            value={audience}
            onChange={(event) => setAudience(event.target.value)}
            style={{
              width: "100%",
              padding: "10px",
              marginTop: "8px",
              fontSize: "16px",
            }}
          >
            <option value="Elementary School">Elementary School</option>
            <option value="Middle School">Middle School</option>
            <option value="High School">High School</option>
            <option value="College">College</option>
          </select>
        </div>
        <div style={{ marginTop: "20px" }}>
          <label htmlFor="videoLength">
            <strong>Video Length:</strong>
          </label>

          <br />

          <select
            id="videoLength"
            value={videoLength}
            onChange={(event) => setVideoLength(event.target.value)}
            style={{
              width: "100%",
              padding: "10px",
              marginTop: "8px",
              fontSize: "16px",
            }}
          >
            <option value="30">30 seconds</option>
            <option value="60">60 seconds</option>
            <option value="90">90 seconds</option>
          </select>
        </div>
        <div style={{ marginTop: "20px" }}>
          <label htmlFor="style">
            <strong>Style:</strong>
          </label>

          <br />

          <select
            id="style"
            value={style}
            onChange={(event) => setStyle(event.target.value)}
            style={{
              width: "100%",
              padding: "10px",
              marginTop: "8px",
              fontSize: "16px",
            }}
          >
            <option value="Educational">Educational</option>
            <option value="Fun">Fun</option>
            <option value="Documentary">Documentary</option>
            <option value="Storytelling">Storytelling</option>
          </select>
        </div>

        <br />

        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: "15px",
            padding: "12px 20px",
            fontSize: "16px",
            cursor: "pointer",
          }}
        >
          {loading ? "Generating Script..." : "Generate Script"}
        </button>
      </form>

      {script && (
        <section style={{ marginTop: "30px", textAlign: "left" }}>
          <h2>{script.title}</h2>

          <h3>Introduction</h3>

          <p>
            <strong>Narration:</strong> {script.introduction.narration}
          </p>

          <p>
            <strong>Visual:</strong> {script.introduction.visual}
          </p>

          {script.scenes.map((scene) => (
            <div key={scene.scene_number} style={{ marginTop: "25px" }}>
            <h3>
              Scene {scene.scene_number}: {scene.title}
            </h3>

            <p>
              <strong>Narration:</strong> {scene.narration}
            </p>

            <p>
              <strong>Visual:</strong> {scene.visual}
            </p>
            </div>
        ))}

          <div style={{ marginTop: "25px" }}>
            <h3>Conclusion</h3>

          <p>
            <strong>Narration:</strong> {script.conclusion.narration}
          </p>

          <p>
            <strong>Visual:</strong> {script.conclusion.visual}
          </p>
          </div>
        </section>
      )}
    </main>
  );
}

export default App;