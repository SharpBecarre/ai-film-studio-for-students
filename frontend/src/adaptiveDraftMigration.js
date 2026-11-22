import {
  readAdaptiveDraft,
} from "./adaptiveDraftStorage.js";

import {
  adaptiveDraftIdentity,
  readAdaptiveCollection,
  saveAdaptiveDraftToCollection,
  findAdaptiveDraftInCollection,
} from "./adaptiveDraftCollection.js";

// Copies a legacy draft into the multi-scene collection.
// Never deletes the original browser-storage entry.
// Never overwrites an existing different draft.

export function migrateLegacyAdaptiveDraft() {
  const legacy = readAdaptiveDraft();

  if (!legacy) {
    return {
      status: "no_legacy_draft",
      migrated: false,
    };
  }

  const collection = readAdaptiveCollection();

  if (!collection) {
    throw new Error(
      "Cannot migrate into an invalid draft collection."
    );
  }

  const key = adaptiveDraftIdentity(legacy);
  const existing = findAdaptiveDraftInCollection(legacy);

  if (existing) {
    if (
      JSON.stringify(existing) !== JSON.stringify(legacy)
    ) {
      return {
        status: "conflict",
        migrated: false,
        key,
      };
    }

    return {
      status: "already_present",
      migrated: false,
      key,
    };
  }

  saveAdaptiveDraftToCollection(legacy);

  const copied = findAdaptiveDraftInCollection(legacy);

  if (
    !copied ||
    JSON.stringify(copied) !== JSON.stringify(legacy)
  ) {
    throw new Error(
      "Migration verification failed."
    );
  }

  return {
    status: "migrated",
    migrated: true,
    key,
  };
}
