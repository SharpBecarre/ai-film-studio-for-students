import {
  isValidAdaptiveDraft,
} from "./adaptiveDraftStorage.js";

// Separate storage from the original single-draft system.
// All browser drafts remain untrusted until backend verification.

export const ADAPTIVE_COLLECTION_KEY =
  "ai-film-studio-adaptive-drafts-v2";

export function adaptiveDraftIdentity(draft) {
  if (!isValidAdaptiveDraft(draft)) {
    throw new Error("Invalid adaptive draft identity.");
  }

  return [
    draft.storyboard_fingerprint,
    draft.scene_number,
    draft.strategy,
    draft.timing_sha256,
  ].join(":");
}

export function isValidAdaptiveCollection(collection) {
  if (
    !collection ||
    typeof collection !== "object" ||
    Array.isArray(collection) ||
    collection.schema_version !== 2 ||
    !collection.drafts ||
    typeof collection.drafts !== "object" ||
    Array.isArray(collection.drafts)
  ) {
    return false;
  }

  return Object.entries(collection.drafts).every(
    ([key, draft]) =>
      isValidAdaptiveDraft(draft) &&
      key === adaptiveDraftIdentity(draft)
  );
}

export function readAdaptiveCollection() {
  try {
    const raw = localStorage.getItem(
      ADAPTIVE_COLLECTION_KEY
    );

    if (!raw) {
      return {
        schema_version: 2,
        drafts: {},
      };
    }

    const parsed = JSON.parse(raw);

    if (!isValidAdaptiveCollection(parsed)) {
      throw new Error("Invalid adaptive draft collection.");
    }

    return parsed;
  } catch (error) {
    console.error(
      "Could not read adaptive draft collection:",
      error
    );
    return null;
  }
}

export function saveAdaptiveDraftToCollection(draft) {
  if (!isValidAdaptiveDraft(draft)) {
    throw new Error("Invalid adaptive draft.");
  }

  const collection = readAdaptiveCollection();

  if (!collection) {
    throw new Error(
      "Existing draft collection is invalid; refusing overwrite."
    );
  }

  const key = adaptiveDraftIdentity(draft);

  const updated = {
    schema_version: 2,
    drafts: {
      ...collection.drafts,
      [key]: draft,
    },
  };

  localStorage.setItem(
    ADAPTIVE_COLLECTION_KEY,
    JSON.stringify(updated)
  );

  return key;
}

export function findAdaptiveDraftInCollection(identity) {
  const key = adaptiveDraftIdentity(identity);
  const collection = readAdaptiveCollection();

  if (!collection) return null;

  return collection.drafts[key] || null;
}
