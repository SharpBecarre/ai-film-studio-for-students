// Browser-only storage for untrusted adaptive planning drafts.
// This module never accesses backend project files.

export const ADAPTIVE_DRAFT_KEY =
  "ai-film-studio-adaptive-draft-v1";

export function isValidAdaptiveDraft(draft) {
  if (!draft || typeof draft !== "object" || Array.isArray(draft)) {
    return false;
  }

  if (draft.schema_version !== 1) {
    return false;
  }

  if (
    typeof draft.storyboard_fingerprint !== "string" ||
    !/^[a-f0-9]{64}$/.test(draft.storyboard_fingerprint)
  ) {
    return false;
  }

  if (
    !Number.isInteger(draft.scene_number) ||
    draft.scene_number < 1
  ) {
    return false;
  }

  if (
    draft.strategy !== "balanced" &&
    draft.strategy !== "cinematic"
  ) {
    return false;
  }

  if (
    typeof draft.timing_sha256 !== "string" ||
    !/^[a-f0-9]{64}$/.test(draft.timing_sha256)
  ) {
    return false;
  }

  if (
    !Array.isArray(draft.clips) ||
    draft.clips.length === 0
  ) {
    return false;
  }

  return draft.clips.every((clip, index) =>
    clip &&
    typeof clip === "object" &&
    clip.clip_number === index + 1 &&
    typeof clip.motion_prompt === "string" &&
    clip.motion_prompt.length <= 900 &&
    typeof clip.prompt_locked === "boolean"
  );
}

export function saveAdaptiveDraft(draft) {
  if (!isValidAdaptiveDraft(draft)) {
    throw new Error("Invalid adaptive draft.");
  }

  localStorage.setItem(
    ADAPTIVE_DRAFT_KEY,
    JSON.stringify(draft)
  );
}

export function readAdaptiveDraft() {
  try {
    const raw = localStorage.getItem(ADAPTIVE_DRAFT_KEY);

    if (!raw) return null;

    const draft = JSON.parse(raw);

    return isValidAdaptiveDraft(draft) ? draft : null;
  } catch (error) {
    console.error("Could not read adaptive draft:", error);
    return null;
  }
}
