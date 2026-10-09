import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("High School");
  const [videoLength, setVideoLength] = useState("60");
  const [style, setStyle] = useState("Educational");

  const [script, setScript] = useState("");
  const [storyboard, setStoryboard] = useState(null);
  const [originalStoryboard, setOriginalStoryboard] = useState(null);

  const [loading, setLoading] = useState(false);
  const [storyboardLoading, setStoryboardLoading] = useState(false);

  

  async function handleSubmit(event) {
    event.preventDefault();

    if (!topic.trim()) {
      alert("Please enter a topic.");
      return;
    }

    setLoading(true);
    setScript("");
    setStoryboard(null);

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
  
  function handleStoryboardChange(sceneNumber, field, newValue) {
    setStoryboard((previousStoryboard) => {
      if (!previousStoryboard) {
        return previousStoryboard;
      }

      return {
        ...previousStoryboard,
        scenes: previousStoryboard.scenes.map((scene) =>
          scene.scene_number === sceneNumber
            ? { ...scene, [field]: newValue }
            : scene
        ),
      };
    });
  }

  function handleResetStoryboard() {
    if (!originalStoryboard) {
      return;
    }

    const confirmed = window.confirm(
      "Reset all storyboard edits to the original AI-generated version?"
    );

    if (confirmed) {
      setStoryboard(originalStoryboard);
    }
  }

  async function handleGenerateStoryboard() {
    if (!script) {
      alert("Please generate a script first.");
      return;
    }


  setStoryboardLoading(true);
  setStoryboard(null);
  setOriginalStoryboard(null);

  try {
    const response = await fetch(
      "http://localhost:8000/generate-storyboard",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          script: script,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok || data.error) {
      alert(data.error || "Could not generate storyboard.");
      return;
    }

    setStoryboard(data);
    setOriginalStoryboard(data);
  } catch (error) {
    alert("Could not connect to the storyboard backend.");
    console.error(error);
  } finally {
    setStoryboardLoading(false);
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

          <button
          type="button"
          onClick={handleGenerateStoryboard}
          disabled={storyboardLoading}
          style={{
            marginTop: "30px",
            padding: "12px 20px",
            fontSize: "16px",
            cursor: storyboardLoading ? "not-allowed" : "pointer",
          }}
        >
          {storyboardLoading ? "Generating Storyboard..." : "Generate Storyboard"}
        </button>
        </section>
      )}

      {storyboard && (
        <section
          style={{
            marginTop: "40px",
            textAlign: "left",
          }}
        >
          
          <h2>Storyboard: {storyboard.title}</h2>
         
          <button
            type="button"
            onClick={handleResetStoryboard}
            style={{
              padding: "10px 18px",
              backgroundColor: "#fff",
              color: "#b91c1c",
              border: "1px solid #b91c1c",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "14px",
              marginTop: "10px",
              marginBottom: "10px",
            }}
          >
            Reset Storyboard
          </button>

          <div
            style={{
              backgroundColor: "#eef4ff",
              border: "1px solid #c7d8f5",
              borderRadius: "10px",
              padding: "15px 20px",
              marginTop: "15px",
              color: "#1e3a5f",
            }}
          >
            <strong>Storyboard Progress</strong>

            <p style={{ marginBottom: "5px" }}>
              {storyboard.scenes.length} of {storyboard.scenes.length} panels planned
            </p>

            <div
              style={{
                width: "100%",
                height: "10px",
                backgroundColor: "#d5e1f2",
                borderRadius: "10px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  backgroundColor: "#2563eb",
                }}
              />
            </div>

            <p style={{ fontSize: "13px", marginBottom: 0 }}>
              Script and visual descriptions ready. Images not yet generated.
            </p>
          </div>


          {storyboard.scenes.map((scene, index) => (
            <div
              key={scene.scene_number}
              style={{
                border: "1px solid #ccc",
                borderRadius: "12px",
                padding: "20px",
                marginTop: "20px",
                backgroundColor: "#f9f9f9",
                color: "#222",
              }}
            >
              <h3>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "15px",
                    marginBottom: "15px",
                  }}
                >
                  <div
                    style={{
                      backgroundColor: "#1e3a5f",
                      color: "white",
                      width: "45px",
                      height: "45px",
                      borderRadius: "10px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: "bold",
                      fontSize: "20px",
                      flexShrink: 0,
                    }}
                  >
                    {index + 1}
                  </div>

                  <div>
                    <div
                      style={{
                        fontSize: "12px",
                        color: "#666",
                        textTransform: "uppercase",
                        letterSpacing: "1px",
                      }}
                    >
                      Storyboard Panel {index + 1}
                    </div>

                    <h3 style={{ margin: "5px 0" }}>
                      {scene.title}
                    </h3>
                  </div>
                </div>
              </h3>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
                  gap: "20px",
                  marginTop: "15px",
                }}
              >
                {/* Visual panel */}
                <div
                  style={{
                    backgroundColor: "#e8f0fe",
                    padding: "20px",
                    borderRadius: "10px",
                  }}
                >
                  <h4>🎬 Visual</h4>

                  {/* Image placeholder */}
                  <div
                    style={{
                      width: "100%",
                      aspectRatio: "16 / 9",
                      backgroundColor: "#d6e3f5",
                      border: "2px dashed #8ba9cc",
                      borderRadius: "8px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      marginBottom: "15px",
                      boxSizing: "border-box",
                    }}
                  >
                    <span
                      style={{
                        color: "#526b89",
                        fontSize: "14px",
                        textAlign: "center",
                      }}
                    >
                      Image will appear here
                    </span>
                  </div>

                  <textarea
                    aria-label={`Visual description for ${scene.title}`}
                    value={scene.visual}
                    onChange={(event) =>
                      handleStoryboardChange(
                        scene.scene_number,
                        "visual",
                        event.target.value
                      )
                    }
                    rows={6}
                    style={{
                      width: "100%",
                      padding: "12px",
                      fontSize: "15px",
                      lineHeight: "1.6",
                      border: "1px solid #ccc",
                      borderRadius: "8px",
                      boxSizing: "border-box",
                      resize: "vertical",
                      fontFamily: "Arial",
                    }}
                  />

                </div>

                {/* Narration panel */}
                <div
                  style={{
                    backgroundColor: "#f0f0f0",
                    padding: "20px",
                    borderRadius: "10px",
                  }}
                >
                  <h4>🎙️ Narration</h4>
                  <textarea
                    aria-label={`Narration for ${scene.title}`}
                    value={scene.narration}
                    onChange={(event) =>
                      handleStoryboardChange(
                        scene.scene_number,
                        "narration",
                        event.target.value
                      )
                    }
                    rows={6}
                    style={{
                      width: "100%",
                      padding: "12px",
                      fontSize: "15px",
                      lineHeight: "1.6",
                      border: "1px solid #ccc",
                      borderRadius: "8px",
                      boxSizing: "border-box",
                      resize: "vertical",
                      fontFamily: "Arial",
                    }}
                  />

                </div>
              </div>
            </div>
          ))}
        </section>
      )}
    </main>
  );
}

export default App;