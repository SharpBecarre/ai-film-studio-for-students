import {
  isValidAdaptiveDraft,
} from "./adaptiveDraftStorage.js";

// Restore editable prompts only after a fresh backend plan
// has been verified against saved narration and existing assets.
// Never trust browser-stored lock flags or protected prompts.

export function restoreVerifiedAdaptiveDraft(
  draft,
  verifiedResponse
) {
  if (!isValidAdaptiveDraft(draft)) {
    throw new Error("Invalid saved adaptive draft.");
  }

  if (
    !verifiedResponse ||
    typeof verifiedResponse !== "object" ||
    !verifiedResponse.shot_plan ||
    !verifiedResponse.specification
  ) {
    throw new Error("A verified backend plan is required.");
  }

  const plan = verifiedResponse.shot_plan;
  const specification = verifiedResponse.specification;

  if (
    draft.storyboard_fingerprint !==
      plan.storyboard_fingerprint ||
    draft.scene_number !== plan.scene_number ||
    draft.strategy !== plan.strategy ||
    draft.timing_sha256 !== plan.timing_sha256 ||
    draft.timing_sha256 !== specification.timing_sha256
  ) {
    throw new Error(
      "Saved draft does not match the current storyboard and timing."
    );
  }

  if (
    !Array.isArray(plan.clips) ||
    draft.clips.length !== plan.clips.length
  ) {
    throw new Error("Saved draft clip count mismatch.");
  }

  const restoredClips = plan.clips.map((clip, index) => {
    const saved = draft.clips[index];

    if (
      !clip ||
      typeof clip !== "object" ||
      clip.clip_number !== index + 1 ||
      saved.clip_number !== clip.clip_number ||
      typeof clip.motion_prompt !== "string" ||
      typeof clip.prompt_locked !== "boolean"
    ) {
      throw new Error("Invalid verified clip structure.");
    }

    // A saved browser draft cannot change an existing
    // protected video clip or its approved motion prompt.
    if (clip.prompt_locked) {
      return { ...clip };
    }

    // Restore only manually edited prompts for unlocked clips.
    if (
      saved.motion_prompt.trim() &&
      saved.motion_prompt.length <= 900 &&
      saved.prompt_locked === false
    ) {
      return {
        ...clip,
        motion_prompt: saved.motion_prompt,
        prompt_source: "manual_edit",
      };
    }

    return { ...clip };
  });

  return {
    ...verifiedResponse,
    shot_plan: {
      ...plan,
      clips: restoredClips,
    },
  };
}
