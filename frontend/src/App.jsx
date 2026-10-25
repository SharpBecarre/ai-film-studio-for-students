import { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [projectTitle, setProjectTitle] = useState("");
  const [audience, setAudience] = useState("High School");
  const [videoLength, setVideoLength] = useState("60");
  const [narrationSpeed, setNarrationSpeed] = useState("150");
  const [style, setStyle] = useState("Educational");

  const [script, setScript] = useState("");
  const [storyboard, setStoryboard] = useState(null);
  const [originalStoryboard, setOriginalStoryboard] = useState(null);

  const [loading, setLoading] = useState(false);
  const [storyboardLoading, setStoryboardLoading] = useState(false);

  function estimateNarrationDuration(text) {
    if (!text || !text.trim()) {
      return 0;
    }

    const wordCount = text.trim().split(/\s+/).length;

    return Math.ceil(
      (wordCount / Number(narrationSpeed)) * 60
    );
  }

  function countNarrationWords(text) {
    if (!text || !text.trim()) {
      return 0;
    }

    return text.trim().split(/\s+/).length;
  }

  function formatNarrationTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${minutes} min ${seconds} sec`;
  }

  function compareNarrationToVideoLength(totalSeconds) {
    const targetSeconds = Number(videoLength);
    const tolerance = targetSeconds * 0.1;

    if (totalSeconds > targetSeconds + tolerance) {
      return "Too long";
    }

    if (totalSeconds < targetSeconds - tolerance) {
      return "Shorter than target";
    }

    return "Within target";
  }

  function calculateDurationPercentage(totalSeconds) {
    const targetSeconds = Number(videoLength);

    if (targetSeconds <= 0) {
      return 0;
    }

    return Math.round((totalSeconds / targetSeconds) * 100);
  }

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
  
  function handleSaveStoryboard() {
    if (!storyboard) {
      alert("Please generate a storyboard first.");
      return;
    }

    try {
      localStorage.setItem(
        "ai-film-studio-storyboard",
        JSON.stringify({
          ...storyboard,
          projectTitle: projectTitle,
          narrationSpeed: narrationSpeed,
          videoLength: videoLength, 
          audience: audience,
          style: style,
        })
      );

      alert("Storyboard saved successfully!");
    } catch (error) {
      console.error("Could not save storyboard:", error);
      alert("Could not save storyboard. Please try again.");
    }
  }

  function handleLoadStoryboard() {
    try {
      const savedStoryboard = localStorage.getItem(
        "ai-film-studio-storyboard"
      );

      if (!savedStoryboard) {
        alert("No saved storyboard found.");
        return;
      }

      const loadedStoryboard = JSON.parse(savedStoryboard);

      setStoryboard(loadedStoryboard);
      setNarrationSpeed(String(loadedStoryboard.narrationSpeed || "150"));
      setProjectTitle(loadedStoryboard.projectTitle || "");
      setVideoLength(String(loadedStoryboard.videoLength || "60"));
      if (loadedStoryboard.audience != null) setAudience(loadedStoryboard.audience);
      if (loadedStoryboard.style != null) setStyle(loadedStoryboard.style);
      setOriginalStoryboard(loadedStoryboard);

      alert("Storyboard loaded successfully!");
    } catch (error) {
      console.error("Could not load storyboard:", error);
      alert("Could not load saved storyboard.");
    }
  }
  
  function handleExportStoryboard() {
    if (!storyboard) {
      alert("Please generate or load a storyboard first.");
      return;
    }

    const storyboardJSON = JSON.stringify({ ...storyboard, projectTitle }, null, 2);

    const blob = new Blob([storyboardJSON], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    const filename = (projectTitle.trim() || storyboard.title || "untitled-storyboard")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");

    link.download = `${filename || "untitled-storyboard"}.json`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }
  
  async function handleImportStoryboard(event) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    try {
      const fileContents = await file.text();
      const importedStoryboard = JSON.parse(fileContents);

      if (
        !importedStoryboard ||
        typeof importedStoryboard.title !== "string" ||
        !Array.isArray(importedStoryboard.scenes) ||
        importedStoryboard.scenes.length === 0 ||
        !importedStoryboard.scenes.every(
          (scene) =>
            typeof scene.scene_number === "number" &&
            typeof scene.title === "string" &&
            typeof scene.narration === "string" &&
            typeof scene.visual === "string"
        )
      ) {
        alert("Invalid storyboard file.");
        return;
      }

      setStoryboard(importedStoryboard);
      setProjectTitle(importedStoryboard.projectTitle || "");
      setOriginalStoryboard(importedStoryboard);

      alert("Storyboard imported successfully!");
    } catch (error) {
      console.error("Could not import storyboard:", error);
      alert("Could not import storyboard. Please select a valid JSON file.");
    } finally {
      event.target.value = "";
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

      <button
            type="button"
            onClick={handleLoadStoryboard}
            style={{
              padding: "10px 18px",
              backgroundColor: "#16a34a",
              color: "white",
              border: "1px solid #16a34a",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "14px",
              marginTop: "10px",
              marginBottom: "10px",
              marginLeft: "10px",
            }}
          >
            Load Storyboard
          </button>
        
          <label
            style={{
              display: "inline-block",
              padding: "10px 18px",
              backgroundColor: "#0891b2",
              color: "white",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "14px",
              marginTop: "10px",
              marginBottom: "10px",
              marginLeft: "10px",
            }}
          >
            Import Storyboard
            <input
              type="file"
              accept=".json,application/json"
              onChange={handleImportStoryboard}
              style={{ display: "none" }}
            />
          </label>


      <p>Turn any educational topic into a short narrated video using AI.</p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "20px" }}>
          <label htmlFor="project-title">
            <strong>Project Title:</strong>
          </label>

          <br />

          <input
            id="project-title"
            type="text"
            value={projectTitle}
            onChange={(event) => setProjectTitle(event.target.value)}
            placeholder="Example: The Future Is Here"
            style={{
              width: "100%",
              padding: "12px",
              marginTop: "10px",
              fontSize: "16px",
              boxSizing: "border-box",
            }}
          />
        </div>
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
          
          <div style={{ marginTop: "15px", marginBottom: "15px" }}>
            <label
              htmlFor="narration-speed"
              style={{
                display: "block",
                marginBottom: "6px",
                fontWeight: "bold",
              }}
            >
              Narration Speed
            </label>

            <select
              id="narration-speed"
              value={narrationSpeed}
              onChange={(e) => setNarrationSpeed(e.target.value)}
              style={{
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                width: "100%",
              }}
            >
              <option value="120">Slow — 120 words/minute</option>
              <option value="150">Normal — 150 words/minute</option>
              <option value="180">Fast — 180 words/minute</option>
            </select>
          </div>
          <div
            style={{
              marginTop: "20px",
              padding: "15px",
              backgroundColor: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: "8px",
            }}
          >
            <h3 style={{ marginTop: 0 }}>
              Project Settings 
            </h3>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 220px), 1fr))",
                gap: "12px",
              }}
            >
            <p style={{ gridColumn: "1 / -1", margin: 0 }}>
              <strong>Project Title:</strong> {projectTitle || "Untitled Project"}
            </p>  
            <p
              style={{
                fontSize: "14px",
                color: "#475569",
                backgroundColor: "#ffffff",
                padding: "12px",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                borderRadius: "8px",
                boxShadow: "0 2px 6px rgba(0, 0, 0, 0.06)",
                margin: 0,
              }}
            >
              <strong>Target Audience:</strong> {audience}
            </p>

            <p
              style={{
                fontSize: "14px",
                color: "#475569",
                backgroundColor: "#ffffff",
                padding: "12px",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                boxShadow: "0 2px 6px rgba(0, 0, 0, 0.06)",
                margin: 0,
              }}
            >
              <strong>Video Length:</strong> {videoLength} seconds
            </p>

            <p
              style={{
                fontSize: "14px",
                color: "#475569",
                backgroundColor: "#ffffff",
                padding: "12px",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                boxShadow: "0 2px 6px rgba(0, 0, 0, 0.06)",
                margin: 0,
              }}
            >
              <strong>Narration Speed:</strong>{" "}
              {narrationSpeed === "120"
                ? "Slow"
                : narrationSpeed === "150"
                ? "Normal"
                : "Fast"}{" "}
              ({narrationSpeed} words/minute)
            </p>

            <p
              style={{
                fontSize: "14px",
                color: "#475569",
                backgroundColor: "#ffffff",
                padding: "12px",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                boxShadow: "0 2px 6px rgba(0, 0, 0, 0.06)",
                margin: 0,
              }}
            >
              <strong>Video Style:</strong> {style}
            </p>
          </div>  
          </div>
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
          
          <p
            style={{
              fontSize: "14px",
              color: "#475569",
              fontWeight: "bold",
              marginTop: "8px",
              marginBottom: "8px",
            }}
          >
            Total narration words:{" "}
            {storyboard.scenes.reduce(
              (total, scene) =>
                total + countNarrationWords(scene.narration),
              0
            )}
          </p>

          <p
            style={{
              fontSize: "14px",
              color: "#2563eb",
              fontWeight: "bold",
              marginTop: "8px",
              marginBottom: "15px",
            }}
          >
            Total estimated narration:{" "}
            {formatNarrationTime(
              storyboard.scenes.reduce(
                (total, scene) =>
                  total + estimateNarrationDuration(scene.narration),
                0
              )
            )}
          </p>

          <p
            style={{
              fontSize: "14px",
              fontWeight: "bold",
              marginTop: "5px",
              marginBottom: "15px",
              color:
                compareNarrationToVideoLength(
                  storyboard.scenes.reduce(
                    (total, scene) =>
                      total + estimateNarrationDuration(scene.narration),
                    0
                  )
                ) === "Within target"
                  ? "#16a34a"
                  : compareNarrationToVideoLength(
                      storyboard.scenes.reduce(
                        (total, scene) =>
                          total + estimateNarrationDuration(scene.narration),
                        0
                      )
                    ) === "Too long"
                  ? "#dc2626"
                  : "#d97706",

            }}
          >
            Narration length status:{" "}
            {compareNarrationToVideoLength(
              storyboard.scenes.reduce(
                (total, scene) =>
                  total + estimateNarrationDuration(scene.narration),
                0
              )
            )}
          </p>
          
          <div style={{ marginBottom: "20px" }}>
            <p
              style={{
                fontSize: "14px",
                fontWeight: "bold",
                color: "#475569",
                marginBottom: "8px",
              }}
            >
              Narration progress:{" "}
              {calculateDurationPercentage(
                storyboard.scenes.reduce(
                  (total, scene) =>
                    total + estimateNarrationDuration(scene.narration),
                  0
                )
              )}%
            </p>

            <div
              style={{
                width: "100%",
                height: "16px",
                backgroundColor: "#e2e8f0",
                borderRadius: "8px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.min(
                    calculateDurationPercentage(
                      storyboard.scenes.reduce(
                        (total, scene) =>
                          total + estimateNarrationDuration(scene.narration),
                        0
                      )
                    ),
                    100
                  )}%`,
                  height: "100%",
                  backgroundColor:
                    calculateDurationPercentage(
                      storyboard.scenes.reduce(
                        (total, scene) =>
                          total + estimateNarrationDuration(scene.narration),
                        0
                      )
                    ) > 110
                      ? "#dc2626"
                      : calculateDurationPercentage(
                          storyboard.scenes.reduce(
                            (total, scene) =>
                              total + estimateNarrationDuration(scene.narration),
                            0
                          )
                        ) < 90
                      ? "#d97706"
                      : "#16a34a",
                  borderRadius: "8px",
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </div>

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

          <button
            type="button"
            onClick={handleSaveStoryboard}
            style={{
              padding: "10px 18px",
              backgroundColor: "#2563eb",
              color: "white",
              border: "1px solid #2563eb",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "14px",
              marginTop: "10px",
              marginBottom: "10px",
              marginLeft: "10px",
            }}
          >
            Save Storyboard
          </button>
      
          <button
            type="button"
            onClick={handleExportStoryboard}
            style={{
              padding: "10px 18px",
              backgroundColor: "#7c3aed",
              color: "white",
              border: "1px solid #7c3aed",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "14px",
              marginTop: "10px",
              marginBottom: "10px",
              marginLeft: "10px",
            }}
          >
            Export Storyboard
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
                transition: "border-color 0.2s ease",
              }}
              onMouseEnter={(event) => {
                event.currentTarget.style.borderColor = "#2563eb";
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.borderColor = "#ccc";
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
                    <h3
                      style={{
                        margin: "5px 0",
                        fontSize: "20px",
                        fontWeight: "bold",
                        color: "#1e293b",
                        lineHeight: "1.4",
                      }}
                    >
                      {scene.title}
                    </h3>

                    <p
                      style={{
                        margin: "4px 0 0",
                        fontSize: "12px",
                        color: "#64748b",
                      }}
                    >
                      Scene {index + 1} of {storyboard.scenes.length}
                    </p>

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
                    
                    onInput={(event) => {
                      event.currentTarget.style.height = "auto";
                      event.currentTarget.style.height =
                        `${event.currentTarget.scrollHeight}px`;
                    }}

                    rows={6}
                    style={{
                      width: "100%",
                      padding: "12px",
                      fontSize: "15px",
                      lineHeight: "1.6",
                      border: "1px solid #ccc",
                      borderRadius: "8px",
                      boxSizing: "border-box",
                      resize: "none",
                      overflowY: "hidden",
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
                                        
                    onInput={(event) => {
                      event.currentTarget.style.height = "auto";
                      event.currentTarget.style.height =
                        `${event.currentTarget.scrollHeight}px`;
                    }}

                    rows={6}
                    style={{
                      width: "100%",
                      padding: "12px",
                      fontSize: "15px",
                      lineHeight: "1.6",
                      border: "1px solid #ccc",
                      borderRadius: "8px",
                      boxSizing: "border-box",
                      resize: "none",
                      overflowY: "hidden",
                      fontFamily: "Arial",
                    }}
                  />

                  <p
                    style={{
                      textAlign: "right",
                      fontSize: "12px",
                      color: "#64748b",
                      marginTop: "5px",
                    }}
                  >
                    {scene.narration.length} characters
                  </p>
                  
                  <p
                    style={{
                      textAlign: "right",
                      fontSize: "12px",
                      color: "#64748b",
                      marginTop: "4px",
                    }}
                  >
                    {countNarrationWords(scene.narration)} words
                  </p>

                  <p
                    style={{
                      textAlign: "right",
                      fontSize: "12px",
                      color: "#2563eb",
                      marginTop: "4px",
                      fontWeight: "bold",
                    }}
                  >
                    Estimated narration: {formatNarrationTime(estimateNarrationDuration(scene.narration))}
                  </p>

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