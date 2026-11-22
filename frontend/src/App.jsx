import { useEffect, useRef, useState } from "react";
import {
  saveAdaptiveDraft,
  readAdaptiveDraft,
} from "./adaptiveDraftStorage.js";

import {
  restoreVerifiedAdaptiveDraft,
} from "./adaptiveDraftRestore.js";

import {
  migrateLegacyAdaptiveDraft,
} from "./adaptiveDraftMigration.js";

import {
  saveAdaptiveDraftToCollection,
  findAdaptiveDraftInCollection,
} from "./adaptiveDraftCollection.js";


function readAutosave() {
  try {
    const raw = localStorage.getItem("ai-film-studio-autosave");
    if (!raw) return null;

    const saved = JSON.parse(raw);

    if (
      !saved ||
      !saved.storyboard ||
      !Array.isArray(saved.storyboard.scenes) ||
      saved.storyboard.scenes.length === 0
    ) {
      return null;
    }

    return saved;
  } catch (error) {
    console.error("Could not read autosave:", error);
    return null;
  }
}


function App() {
  const [initialAutosave] = useState(readAutosave);
const [topic, setTopic] = useState(
  initialAutosave?.topic || ""
);
const [projectTitle, setProjectTitle] = useState(
  initialAutosave?.projectTitle || ""
);
const [audience, setAudience] = useState(
  initialAutosave?.audience || "High School"
);
const [videoLength, setVideoLength] = useState(
  String(initialAutosave?.videoLength || "60")
);
const [narrationSpeed, setNarrationSpeed] = useState(
  String(initialAutosave?.narrationSpeed || "150")
);
const [style, setStyle] = useState(
  initialAutosave?.style || "Educational"
);

const [script, setScript] = useState(
  initialAutosave?.script || ""
);
const [storyboard, setStoryboard] = useState(
  initialAutosave?.storyboard || null
);
const [originalStoryboard, setOriginalStoryboard] = useState(
  initialAutosave?.storyboard || null
);

  const [loading, setLoading] = useState(false);
  const [storyboardLoading, setStoryboardLoading] = useState(false);
  const [cinematicPlanning, setCinematicPlanning] = useState(false);

  // Optional adaptive cinematic shot planning.
  // This state does not affect the original video-generation workflow.
  const [adaptiveSceneNumber, setAdaptiveSceneNumber] = useState(1);
  const [adaptiveStrategy, setAdaptiveStrategy] = useState("balanced");
  const [adaptiveDurations, setAdaptiveDurations] = useState(null);
  const [adaptiveShotPlan, setAdaptiveShotPlan] = useState(null);
  const [adaptiveLoading, setAdaptiveLoading] = useState(false);
  const [adaptiveError, setAdaptiveError] = useState("");

  // Temporary backend-verified motion-prompt approvals.
  // These are not video approvals and are not persisted.
  const [adaptivePromptApprovals, setAdaptivePromptApprovals] =
    useState({});
  const [adaptiveApprovalLoading, setAdaptiveApprovalLoading] =
    useState(null);
  const [adaptiveApprovalError, setAdaptiveApprovalError] =
    useState("");

  // Runway request preview only — no video generation.
  const [adaptiveRunwayPreview, setAdaptiveRunwayPreview] =
    useState(null);
  const [adaptivePreviewLoading, setAdaptivePreviewLoading] =
    useState(null);
  const [adaptivePreviewError, setAdaptivePreviewError] =
    useState("");

  // References for checking asynchronous approval responses.
  const adaptivePlanRef = useRef(adaptiveShotPlan);
  const adaptiveApprovalRequestRef = useRef(0);
  // Prevent outdated Runway previews from appearing after edits.
  const adaptivePreviewRequestRef = useRef(0);



  // Invalidate temporary approvals whenever the active plan changes.
  // Pending approval responses must not approve an outdated plan.
  useEffect(() => {
    adaptivePlanRef.current = adaptiveShotPlan;
    adaptiveApprovalRequestRef.current += 1;
    adaptivePreviewRequestRef.current += 1;
    setAdaptivePromptApprovals({});
    setAdaptiveApprovalLoading(null);
    setAdaptiveApprovalError("");
    setAdaptiveRunwayPreview(null);
    setAdaptivePreviewLoading(null);
    setAdaptivePreviewError("");
  }, [adaptiveShotPlan]);

  const [videoLoading, setVideoLoading] = useState(false);
  const [generatingImageScene, setGeneratingImageScene] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);


useEffect(() => {
  if (!storyboard) {
    return;
  }

  try {
    localStorage.setItem(
      "ai-film-studio-autosave",
      JSON.stringify({
        storyboard,
        script,
        topic,
        projectTitle,
        narrationSpeed,
        videoLength,
        audience,
        style,
        savedAt: new Date().toISOString(),
      })
    );
  } catch (error) {
    console.error("Storyboard autosave failed:", error);
  }
}, [
  storyboard,
  script,
  topic,
  projectTitle,
  narrationSpeed,
  videoLength,
  audience,
  style,
]);

async function restoreSavedScript() {
  try {
    const response = await fetch("/ai_creativity_v2_script.json");

    if (!response.ok) {
      throw new Error("Saved script not found");
    }

    const savedScript = await response.json();

    if (
      !savedScript.title ||
      !savedScript.introduction ||
      !Array.isArray(savedScript.scenes) ||
      !savedScript.conclusion
    ) {
      throw new Error("Invalid saved script format");
    }

    setScript(savedScript);
    
    alert("Saved documentary script restored successfully.");
  } catch (error) {
    alert(`Could not restore script: ${error.message}`);
  }
}

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

    if (storyboard?.scenes?.length) {
      const confirmed = window.confirm(
        "Generating a new script will replace the current storyboard. " +
        "Make sure you have exported your work. Continue?"
      );

      if (!confirmed) {
        return;
      }
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
          project_title: projectTitle,
          audience: audience,
          video_length: videoLength,
          narration_speed: narrationSpeed,
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
            ? {
                ...scene,
                [field]: newValue,
                ...(field === "visual" ? { image_id: null, image_url: null } : {}),
              }
            : scene
        ),
      };
    });
  }

  function handleCinematicPromptChange(sceneNumber, newPrompt) {
    setStoryboard((previousStoryboard) => {
      if (!previousStoryboard) return previousStoryboard;

      return {
        ...previousStoryboard,
        scenes: previousStoryboard.scenes.map((scene) => {
          if (
            scene.scene_number !== sceneNumber ||
            !scene.cinematic_plan
          ) {
            return scene;
          }

          return {
            ...scene,
            cinematic_plan: {
              ...scene.cinematic_plan,
              motion_prompt: newPrompt,
            },
          };
        }),
      };
    });
  }

  async function handleGenerateSceneImage(sceneNumber, visual) {
    if (!visual?.trim()) {
      alert("Please enter a visual description first.");
      return;
    }

    if (generatingImageScene !== null) {
      return;
    }

    setGeneratingImageScene(sceneNumber);

    try {
      const response = await fetch(
        "http://localhost:8000/generate-storyboard-image",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ visual }),
        }
      );

      if (!response.ok) {
        throw new Error("Image generation failed.");
      }

      const data = await response.json();

      if (!data.image_id || !data.image_url) {
        throw new Error("The backend did not return an image.");
      }

      setStoryboard((previous) => {
        if (!previous) return previous;

        return {
          ...previous,
          scenes: previous.scenes.map((scene) =>
            scene.scene_number === sceneNumber && scene.visual === visual
              ? {
                  ...scene,
                  image_id: data.image_id,
                  image_url: data.image_url,
                }
              : scene
          ),
        };
      });
    } catch (error) {
      console.error("Storyboard image generation failed:", error);
      alert("Could not generate the image. Please try again.");
    } finally {
      setGeneratingImageScene(null);
    }
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
          cinematic_planning: cinematicPlanning,
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





function handleMigrateAdaptiveDraft() {
  try {
    const result = migrateLegacyAdaptiveDraft();

    if (result.status === "migrated") {
      alert(
        "Adaptive draft copied into multi-scene storage. " +
        "The original draft was preserved."
      );
    } else if (result.status === "already_present") {
      alert(
        "This adaptive draft is already in multi-scene storage."
      );
    } else if (result.status === "conflict") {
      alert(
        "Migration stopped: a different draft already exists " +
        "for this scene and timing. Neither draft was changed."
      );
    } else {
      alert("No valid legacy adaptive draft was found.");
    }
  } catch (error) {
    console.error("Adaptive draft migration failed:", error);
    alert(
      error instanceof Error
        ? error.message
        : "Could not migrate adaptive draft."
    );
  }
}

function handleSaveAdaptiveDraft() {
  try {
    const plan = adaptiveShotPlan?.shot_plan;

    if (
      !plan ||
      !adaptiveShotPlan?.specification ||
      !adaptiveDurations
    ) {
      throw new Error("Prepare a verified shot plan first.");
    }

    if (
      plan.storyboard_fingerprint !==
        adaptiveDurations.storyboard_fingerprint ||
      plan.timing_sha256 !==
        adaptiveShotPlan.specification.timing_sha256
    ) {
      throw new Error("Adaptive plan identity mismatch.");
    }

    const draft = {
      schema_version: 1,
      storyboard_fingerprint: plan.storyboard_fingerprint,
      scene_number: plan.scene_number,
      strategy: plan.strategy,
      timing_sha256: plan.timing_sha256,
      clips: plan.clips.map((clip) => ({
        clip_number: clip.clip_number,
        motion_prompt: clip.motion_prompt,
        prompt_locked: clip.prompt_locked,
      })),
    };

    saveAdaptiveDraftToCollection(draft);

    alert(
      "Adaptive draft saved in multi-scene browser storage. " +
      "No backend files or videos were changed."
    );
  } catch (error) {
    console.error("Adaptive draft save failed:", error);
    alert(error.message || "Could not save adaptive draft.");
  }
}

async function handleApproveAdaptivePrompt(clipNumber) {
  const current = adaptivePlanRef.current;
  const plan = current?.shot_plan;

  if (!plan?.clips || !Number.isInteger(clipNumber)) {
    setAdaptiveApprovalError("No valid shot plan is selected.");
    return;
  }

  const clip = plan.clips.find(
    (item) => item.clip_number === clipNumber
  );

  if (!clip || clip.prompt_locked) {
    setAdaptiveApprovalError("This clip cannot be approved.");
    return;
  }

  if (!clip.motion_prompt?.trim()) {
    setAdaptiveApprovalError("Enter a motion prompt first.");
    return;
  }

  if (adaptiveApprovalLoading !== null) {
    return;
  }

  const confirmed = window.confirm(
    `Approve the current motion prompt for Clip ${clipNumber}? ` +
    "This approves prompt text only. No video will be generated."
  );

  if (!confirmed) return;

  const requestVersion = ++adaptiveApprovalRequestRef.current;
  const submittedPlan = structuredClone(plan);
  const submittedPrompt = clip.motion_prompt;

  setAdaptiveApprovalLoading(clipNumber);
  setAdaptiveApprovalError("");

  try {
    const response = await fetch(
      "http://localhost:8000/approve-adaptive-motion-prompt",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_number: plan.scene_number,
          strategy: plan.strategy,
          clip_number: clipNumber,
          shot_plan: submittedPlan,
          confirmed: true,
        }),
      }
    );

    const result = await response.json();

    if (requestVersion !== adaptiveApprovalRequestRef.current) {
      return;
    }

    const latestPlan = adaptivePlanRef.current?.shot_plan;
    const latestClip = latestPlan?.clips?.find(
      (item) => item.clip_number === clipNumber
    );

    if (
      latestPlan !== plan ||
      !latestClip ||
      latestClip.prompt_locked ||
      latestClip.motion_prompt !== submittedPrompt
    ) {
      return;
    }

    if (!response.ok) {
      throw new Error(
        typeof result.detail === "string"
          ? result.detail
          : "Motion-prompt approval failed."
      );
    }

    if (
      result.approved !== true ||
      result.trusted_assets_verified !== true ||
      result.saved_to_disk !== false ||
      result.video_generated !== false ||
      result.approval?.clip_number !== clipNumber
    ) {
      throw new Error("Invalid approval response.");
    }

    setAdaptivePromptApprovals((previous) => ({
      ...previous,
      [clipNumber]: {
        record: result.approval,
        prompt: submittedPrompt,
        plan,
      },
    }));
  } catch (error) {
    if (requestVersion === adaptiveApprovalRequestRef.current) {
      setAdaptiveApprovalError(
        error instanceof Error
          ? error.message
          : "Could not approve motion prompt."
      );
    }
  } finally {
    if (requestVersion === adaptiveApprovalRequestRef.current) {
      setAdaptiveApprovalLoading(null);
    }
  }
}

function handleAdaptivePromptChange(clipNumber, newPrompt) {
  if (
    !Number.isInteger(clipNumber) ||
    clipNumber < 1 ||
    typeof newPrompt !== "string" ||
    newPrompt.length > 900
  ) {
    return;
  }

  // Invalidate pending approvals immediately on an edit.
  adaptiveApprovalRequestRef.current += 1;
  // Invalidate previews when a motion prompt changes.
  adaptivePreviewRequestRef.current += 1;
  setAdaptiveRunwayPreview(null);
  setAdaptivePreviewLoading(null);
  setAdaptivePreviewError("");
  setAdaptivePromptApprovals({});
  setAdaptiveApprovalLoading(null);
  setAdaptiveApprovalError("");

  setAdaptiveShotPlan((current) => {
    if (!current?.shot_plan?.clips) {
      return current;
    }

    const matches = current.shot_plan.clips.filter(
      (clip) => clip.clip_number === clipNumber
    );

    if (
      matches.length !== 1 ||
      matches[0].prompt_locked === true
    ) {
      return current;
    }

    return {
      ...current,
      shot_plan: {
        ...current.shot_plan,
        clips: current.shot_plan.clips.map((clip) =>
          clip.clip_number === clipNumber
            ? {
                ...clip,
                motion_prompt: newPrompt,
                prompt_source: "manual_edit",
              }
            : clip
        ),
      },
    };
  });
}

async function handlePreviewAdaptiveRunway(clipNumber) {
  const current = adaptivePlanRef.current;
  const plan = current?.shot_plan;
  const approved = adaptivePromptApprovals[clipNumber];

  if (!plan?.clips || !Number.isInteger(clipNumber)) {
    setAdaptivePreviewError("No valid shot plan is selected.");
    return;
  }

  const clip = plan.clips.find(
    (item) => item.clip_number === clipNumber
  );

  if (
    !clip ||
    clip.prompt_locked ||
    !approved?.record ||
    approved.plan !== plan ||
    approved.prompt !== clip.motion_prompt
  ) {
    setAdaptivePreviewError(
      "Approve the current motion prompt before previewing."
    );
    return;
  }

  if (adaptivePreviewLoading !== null) {
    return;
  }

  const requestVersion = ++adaptivePreviewRequestRef.current;
  const submittedPlan = structuredClone(plan);
  const submittedPrompt = clip.motion_prompt;

  setAdaptiveRunwayPreview(null);
  setAdaptivePreviewLoading(clipNumber);
  setAdaptivePreviewError("");

  try {
    const response = await fetch(
      "http://localhost:8000/preview-adaptive-runway",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_number: plan.scene_number,
          strategy: plan.strategy,
          clip_number: clipNumber,
          shot_plan: submittedPlan,
          approval: approved.record,
        }),
      }
    );

    const result = await response.json();

    if (requestVersion !== adaptivePreviewRequestRef.current) {
      return;
    }

    const latestPlan = adaptivePlanRef.current?.shot_plan;
    const latestClip = latestPlan?.clips?.find(
      (item) => item.clip_number === clipNumber
    );

    if (
      latestPlan !== plan ||
      !latestClip ||
      latestClip.prompt_locked ||
      latestClip.motion_prompt !== submittedPrompt
    ) {
      return;
    }

    if (!response.ok) {
      throw new Error(
        typeof result.detail === "string"
          ? result.detail
          : "Runway preview failed."
      );
    }

    if (
      result.preview_only !== true ||
      result.generation_submitted !== false ||
      result.provider !== "runway" ||
      result.clip_number !== clipNumber ||
      result.scene_number !== plan.scene_number ||
      result.motion_prompt !== submittedPrompt
    ) {
      throw new Error("Invalid Runway preview response.");
    }

    setAdaptiveRunwayPreview(result);
  } catch (error) {
    if (requestVersion === adaptivePreviewRequestRef.current) {
      setAdaptivePreviewError(
        error instanceof Error
          ? error.message
          : "Could not preview Runway request."
      );
    }
  } finally {
    if (requestVersion === adaptivePreviewRequestRef.current) {
      setAdaptivePreviewLoading(null);
    }
  }
}

async function handlePrepareAdaptiveShots() {
  if (!storyboard?.scenes?.length) {
    setAdaptiveError("Please load a storyboard first.");
    return;
  }

  const scenes = storyboard.scenes;
  const sceneIndex = Number(adaptiveSceneNumber) - 1;

  if (
    !Number.isInteger(sceneIndex) ||
    sceneIndex < 0 ||
    sceneIndex >= scenes.length
  ) {
    setAdaptiveError("Please select a valid scene.");
    return;
  }

  setAdaptiveLoading(true);
  setAdaptiveError("");
  setAdaptiveDurations(null);
  setAdaptiveShotPlan(null);

  try {
    // Read existing saved audio. This endpoint never generates media.
    const durationResponse = await fetch(
      "http://localhost:8000/saved-narration-durations",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenes }),
      }
    );

    const durationData = await durationResponse.json();

    if (!durationResponse.ok) {
      throw new Error(
        durationData.detail ||
        "Saved narration durations are unavailable."
      );
    }

    if (
      durationData.scene_count !== scenes.length ||
      durationData.audio_verified !== true
    ) {
      throw new Error("Saved narration verification failed.");
    }

    const selectedDuration = durationData.durations[sceneIndex];

    if (
      selectedDuration?.scene_number !== sceneIndex + 1 ||
      !Number.isFinite(selectedDuration.duration_seconds) ||
      selectedDuration.duration_seconds <= 0
    ) {
      throw new Error("Invalid saved narration duration.");
    }

    // Inspect existing saved prompts and protected video clips.
    const assetsResponse = await fetch(
      "http://localhost:8000/existing-cinematic-assets",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenes,
          scene_number: sceneIndex + 1,
        }),
      }
    );

    const assetsData = await assetsResponse.json();

    if (!assetsResponse.ok) {
      throw new Error(
        assetsData.detail ||
        "Could not inspect existing cinematic assets."
      );
    }

    if (
      assetsData.read_only !== true ||
      assetsData.scene_number !== sceneIndex + 1 ||
      assetsData.storyboard_fingerprint !==
        durationData.storyboard_fingerprint ||
      !Array.isArray(assetsData.locked_clips) ||
      !assetsData.existing_prompts ||
      typeof assetsData.existing_prompts !== "object"
    ) {
      throw new Error("Existing asset verification failed.");
    }

    // Planning only: no OpenAI, Runway, or media generation.
    const planningResponse = await fetch(
      "http://localhost:8000/prepare-adaptive-shots",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenes,
          scene: scenes[sceneIndex],
          scene_number: sceneIndex + 1,
          narration_duration: selectedDuration.duration_seconds,
          strategy: adaptiveStrategy,
          existing_prompts: assetsData.existing_prompts,
          locked_clips: assetsData.locked_clips,
        }),
      }
    );

    const planningData = await planningResponse.json();

    if (!planningResponse.ok) {
      throw new Error(
        planningData.detail ||
        "Could not prepare adaptive cinematic shots."
      );
    }

    if (
      planningData.ai_executed !== false ||
      planningData.video_generated !== false ||
      planningData.scene_number !== sceneIndex + 1 ||
      planningData.storyboard_fingerprint !==
        durationData.storyboard_fingerprint
    ) {
      throw new Error("Adaptive planning verification failed.");
    }

    // Restore only editable prompts from a matching browser draft.
    // The backend-verified plan remains authoritative.
    let displayPlan = planningData;

    const planIdentity = {
      schema_version: 1,
      storyboard_fingerprint:
        planningData.shot_plan.storyboard_fingerprint,
      scene_number: planningData.shot_plan.scene_number,
      strategy: planningData.shot_plan.strategy,
      timing_sha256: planningData.shot_plan.timing_sha256,
      clips: planningData.shot_plan.clips.map((clip) => ({
        clip_number: clip.clip_number,
        motion_prompt: clip.motion_prompt,
        prompt_locked: clip.prompt_locked,
      })),
    };

    try {
      const savedDraft = findAdaptiveDraftInCollection(
        planIdentity
      );

      if (savedDraft) {
        displayPlan = restoreVerifiedAdaptiveDraft(
          savedDraft,
          planningData
        );
      }
    } catch (restoreError) {
      console.info(
        "Saved adaptive draft not restored:",
        restoreError.message
      );
    }

    setAdaptiveDurations(durationData);
    setAdaptiveShotPlan(displayPlan);
  } catch (error) {
    console.error("Adaptive planning error:", error);
    setAdaptiveError(
      error instanceof Error
        ? error.message
        : "Could not prepare adaptive cinematic shots."
    );
  } finally {
    setAdaptiveLoading(false);
  }
}

async function handleGenerateVideo() {
  if (!storyboard?.scenes?.length) {
    alert("Please generate or load a storyboard first.");
    return;
  }

  setVideoLoading(true);
  setVideoUrl(null);

  try {
    const response = await fetch(
      "http://localhost:8000/generate-video",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          scenes: storyboard.scenes,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`Video generation failed: ${response.status}`);
    }

    const videoBlob = await response.blob();
    const url = URL.createObjectURL(videoBlob);

    setVideoUrl(url);
  } catch (error) {
    console.error("Video generation error:", error);
    alert("Could not generate the video. Please check the backend terminal.");
  } finally {
    setVideoLoading(false);
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
          {!projectTitle.trim() && (
            <p style={{ color: "#64748b", fontSize: "13px", marginTop: "6px" }}>
              Tip: Give your film project a title so it's easy to identify later.
            </p>
          )}
          {projectTitle.trim() && (
            <p style={{ color: "#15803d", fontSize: "13px", marginTop: "6px" }}>
              ✓ Project title entered
            </p>
          )}
          <p style={{ color: "#64748b", fontSize: "12px", marginTop: "6px" }}>
            {projectTitle.length} / 60 characters (recommended)
          </p>
          {projectTitle.length > 60 && (
            <p style={{ color: "#b45309", fontSize: "13px", marginTop: "6px" }}>
              Your project title is longer than the recommended 60 characters.
            </p>
          )}
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
            border: projectTitle.trim() ? "1px solid #cbd5e1" : "2px solid #f59e0b",
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
            <p style={{ gridColumn: "1 / -1", margin: 0, fontSize: "20px", textAlign: "center", backgroundColor: "#eff6ff", padding: "12px", borderRadius: "8px" }}>
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
      
        <button
          type="button"
          onClick={restoreSavedScript}
          style={{
            marginLeft: "10px",
            padding: "12px 20px",
            cursor: "pointer",
          }}
        >
          Restore Saved Script
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

          <label style={{ display: "block", marginTop: "20px" }}>
            <input
              type="checkbox"
              checked={cinematicPlanning}
              onChange={(event) => setCinematicPlanning(event.target.checked)}
              disabled={storyboardLoading}
            />
            {" "}Enable AI Cinematic Planning (uses OpenAI API credits)
          </label>

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
              transition: "background-color 0.2s ease",
              marginTop: "10px",
              marginBottom: "10px",
            }}
            onMouseEnter={(event) => {
              event.currentTarget.style.backgroundColor = "#fff1f2";
            }}
            onMouseLeave={(event) => {
              event.currentTarget.style.backgroundColor = "#fff";
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
              transition: "background-color 0.2s ease",
              marginTop: "10px",
              marginBottom: "10px",
              marginLeft: "10px",
            }}
            onMouseEnter={(event) => {
              event.currentTarget.style.backgroundColor = "#1d4ed8";
            }}
            onMouseLeave={(event) => {
              event.currentTarget.style.backgroundColor = "#2563eb";
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
              transition: "background-color 0.2s ease",
              marginTop: "10px",
              marginBottom: "10px",
              marginLeft: "10px",
            }}
            onMouseEnter={(event) => {
              event.currentTarget.style.backgroundColor = "#6d28d9";
            }}
            onMouseLeave={(event) => {
              event.currentTarget.style.backgroundColor = "#7c3aed";
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
                boxShadow: "0 3px 10px rgba(0, 0, 0, 0.08)",
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
                      boxShadow: "0 2px 6px rgba(0, 0, 0, 0.15)",
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


              {/* AI Cinematic Director plan */}
              <details
                style={{
                  marginTop: "15px",
                  padding: "12px",
                  backgroundColor: "#f0f7ff",
                  border: "1px solid #bfdbfe",
                  borderRadius: "8px",
                }}
              >
                <summary
                  style={{
                    cursor: "pointer",
                    fontWeight: "bold",
                    color: "#1e40af",
                  }}
                >
                  🎥 AI Cinematic Plan
                  {scene.cinematic_plan ? " — Ready" : " — Not available"}
                </summary>

                {scene.cinematic_plan ? (
                  <div style={{ marginTop: "12px", lineHeight: "1.6" }}>
                    <p><strong>Shot:</strong> {scene.cinematic_plan.shot_description}</p>
                    <p><strong>Subject movement:</strong> {scene.cinematic_plan.subject_action}</p>
                    <p><strong>Camera movement:</strong> {scene.cinematic_plan.camera_movement}</p>
                    <label
                      htmlFor={`cinematic-prompt-${scene.scene_number}`}
                      style={{ display: "block", fontWeight: "bold" }}
                    >
                      Runway motion prompt:
                    </label>

                    <textarea
                      id={`cinematic-prompt-${scene.scene_number}`}
                      value={scene.cinematic_plan.motion_prompt}
                      onChange={(event) =>
                        handleCinematicPromptChange(
                          scene.scene_number,
                          event.target.value
                        )
                      }
                      rows={6}
                      maxLength={900}
                      style={{
                        width: "100%",
                        boxSizing: "border-box",
                        padding: "10px",
                        marginTop: "8px",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        fontSize: "14px",
                        lineHeight: "1.6",
                      }}
                    />
                  </div>
                ) : (
                  <p style={{ marginTop: "10px", color: "#64748b" }}>
                    No cinematic plan was returned for this scene.
                  </p>
                )}
              </details>

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
                    {scene.image_id ? (
                      <img
                        src={`http://localhost:8000/storyboard-images/${scene.image_id}`}
                        alt={`Storyboard image for ${scene.title}`}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "contain",
                        }}
                      />
                    ) : (
                      <span
                        style={{
                          color: "#526b89",
                          fontSize: "14px",
                          textAlign: "center",
                        }}
                      >
                        Image will appear here
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() =>
                      handleGenerateSceneImage(scene.scene_number, scene.visual)
                    }
                    disabled={generatingImageScene !== null}
                  >
                    {generatingImageScene === scene.scene_number
                      ? "Generating Image..."
                      : scene.image_id
                        ? "Regenerate Image"
                        : "Generate Image"}
                  </button>

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

      {storyboard?.scenes?.length > 0 && (
        <section
          style={{
            marginTop: "30px",
            padding: "18px",
            border: "1px solid #cbd5e1",
            borderRadius: "10px",
            textAlign: "left",
          }}
        >
          <h2>Adaptive Cinematic Shot Planning (Preview)</h2>

          <p>
            Prepare cinematic shots using existing saved narration.
            This preview does not generate or overwrite media.
          </p>

          <label htmlFor="adaptive-scene-select">
            Scene:
          </label>

          <select
            id="adaptive-scene-select"
            value={adaptiveSceneNumber}
            onChange={(event) => {
              setAdaptiveSceneNumber(Number(event.target.value));
              setAdaptiveDurations(null);
              setAdaptiveShotPlan(null);
              setAdaptiveError("");
            }}
            style={{ display: "block", margin: "8px 0 14px" }}
          >
            {storyboard.scenes.map((scene, index) => (
              <option key={index} value={index + 1}>
                {index + 1}. {scene.title}
              </option>
            ))}
          </select>

          <label htmlFor="adaptive-strategy-select">
            Planning strategy:
          </label>

          <select
            id="adaptive-strategy-select"
            value={adaptiveStrategy}
            onChange={(event) => {
              setAdaptiveStrategy(event.target.value);
              setAdaptiveShotPlan(null);
              setAdaptiveError("");
            }}
            style={{ display: "block", margin: "8px 0 14px" }}
          >
            <option value="balanced">Balanced</option>
            <option value="cinematic">Cinematic</option>
          </select>

          <button
            type="button"
            onClick={handlePrepareAdaptiveShots}
            disabled={adaptiveLoading}
          >
            {adaptiveLoading
              ? "Preparing..."
              : "Prepare Cinematic Shots"}
          </button>

          {adaptiveError && (
            <p role="alert" style={{ color: "#b91c1c" }}>
              {adaptiveError}
            </p>
          )}

          {adaptiveShotPlan && adaptiveDurations && (
            <div style={{ marginTop: "18px" }}>
              <h3>Prepared Shot Plan</h3>

              <p>
                Verified narration duration:{" "}
                <strong>
                  {adaptiveDurations.durations[
                    adaptiveShotPlan.scene_number - 1
                  ]?.duration_seconds.toFixed(2)} seconds
                </strong>
              </p>

              <p>
                Scene: {adaptiveShotPlan.scene_number}
              </p>

              <p>
                AI executed:{" "}
                {adaptiveShotPlan.ai_executed ? "Yes" : "No"}
              </p>

              <p>
                Video generated:{" "}
                {adaptiveShotPlan.video_generated ? "Yes" : "No"}
              </p>


              <div style={{ marginTop: "20px" }}>
                <h3>Adaptive Clip Motion Prompts</h3>
                <button
                  type="button"
                  onClick={handleSaveAdaptiveDraft}
                  style={{ marginBottom: "12px" }}
                >
                  Save Adaptive Draft (Browser Only)
                </button>

                <button
                  type="button"
                  onClick={handleMigrateAdaptiveDraft}
                  style={{
                    marginLeft: "8px",
                    marginBottom: "12px",
                  }}
                >
                  Copy Existing Draft to Multi-Scene Storage
                </button>


                <p style={{ fontSize: "13px", color: "#475569" }}>
                  Changes are temporary and remain in this browser
                  session. No files are saved or videos generated.
                </p>

                {adaptiveShotPlan.shot_plan.clips.map((clip) => (
                  <div
                    key={clip.clip_number}
                    style={{
                      marginTop: "14px",
                      padding: "14px",
                      border: "1px solid #cbd5e1",
                      borderRadius: "8px",
                    }}
                  >
                    <p style={{ fontWeight: "bold" }}>
                      Clip {clip.clip_number} —{" "}
                      {clip.duration_seconds} seconds
                    </p>

                    <p style={{ fontSize: "13px" }}>
                      Status:{" "}
                      {clip.prompt_locked
                        ? "Locked — existing video protected"
                        : "Editable — not locked"}
                    </p>

                    <label
                      htmlFor={`adaptive-prompt-${clip.clip_number}`}
                      style={{
                        display: "block",
                        marginBottom: "6px",
                        fontWeight: "bold",
                      }}
                    >
                      Motion prompt
                    </label>

                    <textarea
                      id={`adaptive-prompt-${clip.clip_number}`}
                      value={clip.motion_prompt}
                      readOnly={clip.prompt_locked}
                      maxLength={900}
                      rows={6}
                      onChange={(event) =>
                        handleAdaptivePromptChange(
                          clip.clip_number,
                          event.target.value
                        )
                      }
                      style={{
                        width: "100%",
                        boxSizing: "border-box",
                        padding: "10px",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        backgroundColor: clip.prompt_locked
                          ? "#f1f5f9"
                          : "#ffffff",
                        fontSize: "14px",
                        lineHeight: "1.5",
                      }}
                    />

                    <p style={{ fontSize: "12px", color: "#64748b" }}>
                      {(clip.motion_prompt || "").length}/900 characters
                    </p>

                    <button
                      type="button"
                      onClick={() =>
                        handleApproveAdaptivePrompt(clip.clip_number)
                      }
                      disabled={
                        clip.prompt_locked ||
                        !clip.motion_prompt?.trim() ||
                        adaptiveApprovalLoading !== null ||
                        adaptiveLoading
                      }
                      style={{ marginTop: "8px" }}
                    >
                      {adaptiveApprovalLoading === clip.clip_number
                        ? "Approving..."
                        : "Approve Motion Prompt"}
                    </button>

                    {adaptivePromptApprovals[clip.clip_number]?.plan ===
                      adaptiveShotPlan.shot_plan &&
                      adaptivePromptApprovals[clip.clip_number]?.prompt ===
                        clip.motion_prompt && (
                        <p
                          role="status"
                          style={{
                            color: "#166534",
                            fontSize: "13px",
                          }}
                        >
                          Motion prompt approved for this session.
                          No video generated.
                        </p>
                      )}
                    {adaptivePromptApprovals[clip.clip_number]?.plan ===
                      adaptiveShotPlan.shot_plan &&
                      adaptivePromptApprovals[clip.clip_number]?.prompt ===
                        clip.motion_prompt && (
                        <button
                          type="button"
                          onClick={() =>
                            handlePreviewAdaptiveRunway(clip.clip_number)
                          }
                          disabled={
                            adaptivePreviewLoading !== null ||
                            adaptiveApprovalLoading !== null ||
                            adaptiveLoading
                          }
                          style={{ marginTop: "8px", marginLeft: "8px" }}
                        >
                          {adaptivePreviewLoading === clip.clip_number
                            ? "Preparing Preview..."
                            : "Preview Runway Request"}
                        </button>
                      )}
                    {adaptiveRunwayPreview?.scene_number ===
                      adaptiveShotPlan.shot_plan.scene_number &&
                      adaptiveRunwayPreview?.clip_number ===
                        clip.clip_number &&
                      adaptiveRunwayPreview?.motion_prompt ===
                        clip.motion_prompt && (
                        <div
                          role="status"
                          style={{
                            marginTop: "12px",
                            padding: "12px",
                            border: "1px solid #cbd5e1",
                            borderRadius: "6px",
                            backgroundColor: "#f8fafc",
                            fontSize: "13px",
                          }}
                        >
                          <strong>Verified Runway Request Preview</strong>

                          <p>Model: {adaptiveRunwayPreview.model}</p>
                          <p>
                            Duration: {adaptiveRunwayPreview.duration_seconds} seconds
                          </p>
                          <p>Resolution: {adaptiveRunwayPreview.ratio}</p>
                          <p>Scene: {adaptiveRunwayPreview.scene_number}</p>
                          <p>Clip: {adaptiveRunwayPreview.clip_number}</p>

                          <p>
                            <strong>Motion prompt:</strong>
                          </p>
                          <p style={{ whiteSpace: "pre-wrap" }}>
                            {adaptiveRunwayPreview.motion_prompt}
                          </p>

                          <p>
                            <strong>Image SHA-256:</strong>{" "}
                            <code style={{ overflowWrap: "anywhere" }}>
                              {adaptiveRunwayPreview.image_sha256}
                            </code>
                          </p>

                          <p>
                            <strong>Prompt SHA-256:</strong>{" "}
                            <code style={{ overflowWrap: "anywhere" }}>
                              {adaptiveRunwayPreview.prompt_sha256}
                            </code>
                          </p>

                          <p style={{ color: "#166534", fontWeight: "bold" }}>
                            Preview only — no video generated or submitted.
                          </p>
                        </div>
                      )}

                    {adaptivePreviewError && (
                      <p role="alert" style={{ color: "#b91c1c" }}>
                        {adaptivePreviewError}
                      </p>
                    )}

                    {adaptiveApprovalError && (
                      <p
                        role="alert"
                        style={{
                          color: "#b91c1c",
                          fontSize: "13px",
                        }}
                      >
                        {adaptiveApprovalError}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              <details>
                <summary>View proposed shot plan and timing</summary>
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                    fontSize: "12px",
                  }}
                >
                  {JSON.stringify(
                    {
                      specification: adaptiveShotPlan.specification,
                      shot_plan: adaptiveShotPlan.shot_plan,
                      preparation: adaptiveShotPlan.preparation,
                    },
                    null,
                    2
                  )}
                </pre>
              </details>

              <details>
                <summary>View AI prompt instructions (not executed)</summary>
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                    fontSize: "12px",
                  }}
                >
                  {JSON.stringify(
                    adaptiveShotPlan.ai_prompt,
                    null,
                    2
                  )}
                </pre>
              </details>
            </div>
          )}
        </section>
      )}

      {storyboard && (
        <section style={{ marginTop: "30px", marginBottom: "30px" }}>
          <h2>Generate Your Video</h2>

          <button
            onClick={handleGenerateVideo}
            disabled={videoLoading}
          >
            {videoLoading ? "Generating Video..." : "Generate Video"}
          </button>

          {videoLoading && (
            <p>Creating scenes and AI narration. Please wait...</p>
          )}

          {videoUrl && (
            <div style={{ marginTop: "20px" }}>
              <h3>Your Generated Video</h3>

              <video
                src={videoUrl}
                controls
                style={{ width: "100%", maxWidth: "800px" }}
              />

              <div style={{ marginTop: "15px" }}>
                <a
                  href={videoUrl}
                  download="ai_film_studio_video.mp4"
                >
                  Download MP4
                </a>
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

export default App;