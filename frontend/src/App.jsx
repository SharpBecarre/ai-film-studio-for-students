import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    alert(`Video topic: ${topic}`);
  }

  return (
    <main style={{ padding: "40px", fontFamily: "Arial", maxWidth: "700px" }}>
      <h1>AI Film Studio for Students</h1>

      <p>
        Turn any educational topic into a short narrated video using AI.
      </p>

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
          Generate Video Plan
        </button>
      </form>

      {topic && (
        <section style={{ marginTop: "30px" }}>
          <h2>Current Topic</h2>
          <p>{topic}</p>
        </section>
      )}
    </main>
  );
}

export default App;