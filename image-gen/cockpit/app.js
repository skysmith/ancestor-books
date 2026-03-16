const statusLabels = {
  draft: "Draft",
  "needs-work": "Needs work",
  approved: "Approved",
  missing: "Missing asset",
};

const artStateLabels = {
  approved: "Approved",
  candidate: "Candidate",
  assigned: "Assigned",
  draft: "Draft",
};

const fallbackPalette = {
  span: "linear-gradient(135deg, #e0f2fe, #fef3c7)",
  left: "linear-gradient(135deg, #ede9fe, #fee2e2)",
  right: "linear-gradient(135deg, #fef2f2, #f9fafb)",
  inset: "linear-gradient(135deg, #ecfccb, #dbeafe)",
  "text-only": "linear-gradient(135deg, #f5f3ff, #ede9fe)",
};

const STORY_ROLE_OPTIONS = [
  "",
  "opening",
  "setup",
  "rising_action",
  "turn",
  "climax",
  "aftermath",
  "resolution",
  "closing_image",
];

const BEAT_TYPE_OPTIONS = [
  "",
  "environment",
  "dialogue",
  "action",
  "reaction",
  "suspense",
  "object_focus",
  "reflection",
];

const MANUSCRIPT_ILLUSTRATION_FIELDS = new Set([
  "prompt",
  "story_role",
  "beat_type",
  "spread_intent",
  "emotional_state",
  "visual_focus",
  "page_turn_tension",
  "illustration_notes",
]);

const NEW_PROJECT_VALUE = "__new_project__";
const ACTIVE_TAB_STORAGE_KEY = "imageGenDashboard.activeTab";
const JUDGE_PRESETS = {
  1: { threshold: 0.62, label: "1. Loose pass", description: "Keeps momentum and accepts rough early drafts." },
  2: { threshold: 0.72, label: "2. Gentle critic", description: "Catches obvious misses without slowing you down much." },
  3: { threshold: 0.78, label: "3. Balanced", description: "A solid quality gate for normal runs." },
  4: { threshold: 0.86, label: "4. Exacting", description: "Pushes for stronger composition and consistency." },
  5: { threshold: 0.93, label: "5. Director mode", description: "Only near-final work gets through." },
};

const TINY_MAGIC_BOOK_TEST = {
  title: "The Lantern in the Rain",
  story:
    "A very short picture-book test. A shy child walks home in the rain carrying a paper lantern for her grandmother. The wind tries to blow it out, but she protects it with her coat and keeps going. At the end, she reaches the warm house, the lantern is still glowing, and her grandmother smiles at the door.",
};

let spreads = [];
let assets = [];
const imageDimensionCache = new Map();
let generationConfig = {};
let activeSpreadId = null;
let statusPollTimer = null;
let lastStatus = null;
let overlayDragState = null;
let availableProjects = [];
let currentProjectId = "";
let referenceInboxItems = [];
let ollamaModels = [];
let manuscriptData = { documents: [], prompts: [], sources: [] };
let activeManuscriptDocId = "";
let manuscriptDocEditing = false;
let manuscriptDocDraft = "";
let setupStatus = null;
let projectPickerOpen = false;
let manuscriptGenerationConfig = null;
let manuscriptGenerationStatus = null;
let lastManuscriptStatusUpdatedAt = "";

const refs = {};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  cacheElements();
  initializeDrawerPanels();
  attachListeners();
  showTab(loadActiveTabPreference(), { persist: false });
  await refreshProjects();
  await refreshData();
  await refreshReferenceInbox();
  await refreshManuscriptData();
  await refreshOllamaModels();
  await refreshSetupStatus();
  startStatusPoll();
}

function loadActiveTabPreference() {
  try {
    const value = window.localStorage.getItem(ACTIVE_TAB_STORAGE_KEY);
    return ["layout", "generate", "assets", "manuscript"].includes(value || "") ? value : "layout";
  } catch (_err) {
    return "layout";
  }
}

function saveActiveTabPreference(name) {
  try {
    window.localStorage.setItem(ACTIVE_TAB_STORAGE_KEY, name);
  } catch (_err) {
    // Ignore storage failures and keep the session usable.
  }
}

function cacheElements() {
  const ids = [
    "spreadGrid",
    "drawerTitle",
    "spreadPreview",
    "previewOverlay",
    "dropTarget",
    "dropTargetCopy",
    "approveCandidateBtn",
    "promptField",
    "referenceNotesField",
    "negativeField",
    "seedField",
    "notesField",
    "statusSelect",
    "promptStatus",
    "uploadStatus",
    "lastUpdated",
    "assetSelect",
    "generationStatus",
    "generationStatusMeta",
    "generationLog",
    "abortGeneratorBtn",
    "projectSelect",
    "projectSelectButton",
    "projectSelectLabel",
    "projectSelectMenu",
    "manuscriptDocTabs",
    "manuscriptDocTitle",
    "manuscriptDocHelper",
    "manuscriptDocActions",
    "manuscriptDocBody",
    "manuscriptDocEditor",
    "manuscriptDocStatus",
    "manuscriptPromptCards",
    "manuscriptSourceList",
    "manuscriptUploadStatus",
    "manuscriptSourceLink",
    "manuscriptSourceText",
    "manuscriptProvider",
    "manuscriptOpenAIModel",
    "manuscriptLocalModel",
    "manuscriptUseEnvKey",
    "manuscriptApiKey",
    "manuscriptProviderBadge",
    "manuscriptGenerationSummary",
    "manuscriptGenerationStatus",
    "saveManuscriptConfigBtn",
    "generateManuscriptBtn",
    "spreadReferences",
    "referenceInbox",
    "fullscreenLeftTitle",
    "fullscreenRightTitle",
    "generateSpreadSelect",
    "generatePrompt",
    "generateNegative",
    "generateSeed",
    "judgeModel",
    "judgeThreshold",
    "judgeThresholdHelp",
    "maxFails",
    "promptStrategy",
    "allowUpdates",
    "drawerJudgeModel",
    "drawerJudgeThreshold",
    "drawerJudgeThresholdHelp",
    "drawerMaxFails",
    "drawerPromptStrategy",
    "drawerAllowUpdates",
    "snapOverlayBtn",
    "clearJudgeOverridesBtn",
    "fullscreenToggleOverlay",
    "setupStatusSummary",
    "setupStatusModels",
    "setupStatusPaths",
    "setupStatusMeta",
    "setupStatusBadge",
    "projectModal",
    "newProjectTitle",
    "newProjectStory",
    "newProjectOvernight",
    "newProjectStatus",
    "loadTinyMagicBookBtn",
    "magicBookProgressCard",
    "magicBookProgressBadge",
    "magicBookProgressText",
    "magicBookSteps",
    "magicBookProgressHint",
  ];
  ids.forEach((id) => {
    refs[id] = document.getElementById(id);
  });
  refs.layoutGrid = document.getElementById("spreadGrid");
  refs.drawerPanels = document.querySelectorAll(".drawer-panel");
  refs.tabButtons = document.querySelectorAll(".tabs .tab");
  refs.layoutView = document.getElementById("layoutView");
  refs.generateView = document.getElementById("generateView");
  refs.assetsView = document.getElementById("assetsView");
  refs.manuscriptView = document.getElementById("manuscriptView");
  refs.placeRadios = document.querySelectorAll('input[name="placement"]');
  refs.overlayVisible = document.getElementById("overlayVisible");
  refs.overlayX = document.getElementById("overlayX");
  refs.overlayY = document.getElementById("overlayY");
  refs.overlayWidth = document.getElementById("overlayWidth");
  refs.overlayAlignment = document.getElementById("overlayAlignment");
  refs.overlayWash = document.getElementById("overlayWash");
  refs.assetList = document.getElementById("assetsList");
  refs.assetControls = document.getElementById("assetSelect");
  refs.overlayTextLeft = document.getElementById("fullscreenLeftOverlay");
  refs.overlayTextRight = document.getElementById("fullscreenRightOverlay");
  refs.fullscreenSpreadOverlay = document.getElementById("fullscreenSpreadOverlay");
  refs.fullscreen = document.getElementById("fullscreenOverlay");
  refs.fullscreenPages = document.querySelector(".fullscreen-pages");
  refs.fullscreenPageLeft = document.querySelector(".fullscreen-page.left");
  refs.fullscreenPageRight = document.querySelector(".fullscreen-page.right");
  refs.fullscreenLeft = document.getElementById("fullscreenLeft");
  refs.fullscreenRight = document.getElementById("fullscreenRight");
  refs.generateLog = document.getElementById("generationLog");
  refs.generateStatus = document.getElementById("generationStatus");
  refs.closeProjectModal = document.getElementById("closeProjectModal");
  refs.createProjectBtn = document.getElementById("createProjectBtn");
  refs.projectSelectShell = document.getElementById("projectSelectShell");
  populateJudgePresetSelect(refs.judgeThreshold);
  populateJudgePresetSelect(refs.drawerJudgeThreshold);
}

function initializeDrawerPanels() {
  refs.drawerPanels?.forEach((panel) => {
    const toggle = panel.querySelector(".drawer-panel-toggle");
    if (!toggle) return;
    const expanded = toggle.getAttribute("aria-expanded") !== "false";
    panel.classList.toggle("is-collapsed", !expanded);
    toggle.addEventListener("click", () => {
      const nextExpanded = toggle.getAttribute("aria-expanded") === "false";
      toggle.setAttribute("aria-expanded", String(nextExpanded));
      panel.classList.toggle("is-collapsed", !nextExpanded);
    });
  });
}

function attachListeners() {
  refs.projectSelectButton?.addEventListener("click", () => toggleProjectPicker());
  refs.projectSelectMenu?.addEventListener("click", async (event) => {
    const option = event.target.closest("[data-project-id]");
    if (!option) return;
    const nextProjectId = option.dataset.projectId || "";
    closeProjectPicker();
    if (nextProjectId === NEW_PROJECT_VALUE) {
      toggleProjectModal(true);
      return;
    }
    if (!nextProjectId || nextProjectId === currentProjectId) return;
    await loadProject(nextProjectId);
    activeSpreadId = null;
    await refreshProjects();
    await refreshData();
    await refreshManuscriptData();
  });

  refs.closeProjectModal?.addEventListener("click", () => toggleProjectModal(false));
  refs.projectModal?.addEventListener("click", (event) => {
    if (event.target === refs.projectModal) {
      toggleProjectModal(false);
    }
  });
  refs.createProjectBtn?.addEventListener("click", () => createMagicProject());
  refs.loadTinyMagicBookBtn?.addEventListener("click", () => loadTinyMagicBookTest());

  document.addEventListener("click", (event) => {
    if (!projectPickerOpen) return;
    if (refs.projectSelectShell?.contains(event.target)) return;
    closeProjectPicker();
  });

  [refs.drawerJudgeModel, refs.judgeModel].forEach((select) => {
    select?.addEventListener("focus", () => refreshOllamaModels());
    select?.addEventListener("pointerdown", () => refreshOllamaModels());
  });

  refs.layoutGrid.addEventListener("click", (event) => {
    const openButton = event.target.closest("[data-action='open-spread']");
    const tile = event.target.closest(".spread-tile");
    if (!tile) return;
    const focusDrawer = !openButton;
    selectSpread(tile.dataset.id, { focusDrawer });
    if (openButton) {
      event.preventDefault();
      openFullscreen();
    }
  });

  refs.layoutGrid.addEventListener("dblclick", (event) => {
    const tile = event.target.closest(".spread-tile");
    if (!tile) return;
    selectSpread(tile.dataset.id, { focusDrawer: true });
    openFullscreen();
  });

  refs.layoutGrid.addEventListener("keydown", (event) => {
    const tile = event.target.closest(".spread-tile");
    if (!tile) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectSpread(tile.dataset.id, { focusDrawer: true });
      openFullscreen();
    }
  });

  refs.promptField.addEventListener("input", () => saveSpreadField("prompt", refs.promptField.value));
  refs.referenceNotesField?.addEventListener("input", () => saveSpreadField("reference_notes", refs.referenceNotesField.value));
  refs.negativeField.addEventListener("input", () => saveSpreadField("negative_prompt", refs.negativeField.value));
  refs.seedField.addEventListener("input", () => saveSpreadField("seed", refs.seedField.value));
  refs.notesField.addEventListener("input", () => saveSpreadField("notes", refs.notesField.value));
  refs.statusSelect.addEventListener("change", () => saveSpreadField("status", refs.statusSelect.value, true));

  refs.placeRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
      if (!radio.checked) return;
      saveSpreadField("layout_type", radio.value, true);
    });
  });

  [
    refs.overlayVisible,
    refs.overlayX,
    refs.overlayY,
    refs.overlayWidth,
    refs.overlayAlignment,
    refs.overlayWash,
  ].forEach((control) => {
    control.addEventListener("input", () => {
      const spread = spreads.find((item) => item.spread_id === activeSpreadId);
      if (!spread) return;
      const overlay = {
        visible: refs.overlayVisible.checked,
        x: Number(refs.overlayX.value),
        y: Number(refs.overlayY.value),
        width: Number(refs.overlayWidth.value),
        alignment: refs.overlayAlignment.value,
        wash_opacity: Number(refs.overlayWash.value),
      };
      spread.text_overlay = overlay;
      updateOverlayVisual(spread);
      updateFullscreenOverlay(spread);
      saveSpreadField("text_overlay", overlay);
    });
  });

  refs.snapOverlayBtn?.addEventListener("click", () => snapOverlayToSafeMargin());

  attachOverlayDragTargets();

  document.getElementById("assignAssetBtn").addEventListener("click", async () => {
    const assetId = refs.assetControls.value;
    if (!assetId) return;
    await assignAsset(assetId);
  });

  document.getElementById("uploadBtn").addEventListener("click", () => document.getElementById("hiddenUpload").click());
  document.getElementById("approveCandidateBtn").addEventListener("click", () => approveCandidate());
  document.getElementById("hiddenUpload").addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileUpload(file);
      event.target.value = "";
    }
  });

  if (refs.dropTarget) {
    ["dragenter", "dragover"].forEach((name) => {
      refs.dropTarget.addEventListener(name, (event) => {
        event.preventDefault();
        refs.dropTarget.classList.add("drag-over");
      });
    });
    ["dragleave", "dragend"].forEach((name) => {
      refs.dropTarget.addEventListener(name, () => refs.dropTarget.classList.remove("drag-over"));
    });
    refs.dropTarget.addEventListener("drop", (event) => {
      event.preventDefault();
      refs.dropTarget.classList.remove("drag-over");
      const file = event.dataTransfer?.files?.[0];
      if (file) {
        handleFileUpload(file);
      }
    });
  }

  document.getElementById("launchGeneratorBtn").addEventListener("click", () => {
    showTab("generate");
    refs.generateSpreadSelect.value = activeSpreadId;
    loadGenerationForm();
  });

  document.getElementById("fullscreenToggle").addEventListener("click", () => {
    openFullscreen();
  });
  document.getElementById("closeFullscreen").addEventListener("click", () => {
    closeFullscreen();
  });
  document.getElementById("fullscreenToggleOverlay").addEventListener("click", () => {
    toggleOverlayVisibility();
  });

  refs.tabButtons.forEach((button) => {
    button.addEventListener("click", () => showTab(button.dataset.tab));
  });

  refs.drawerJudgeModel?.addEventListener("change", () => saveSpreadGenerationOverride("judge_model", refs.drawerJudgeModel.value));
  refs.drawerJudgeThreshold?.addEventListener("input", () =>
    saveSpreadGenerationOverride("judge_threshold", presetToThreshold(refs.drawerJudgeThreshold.value))
  );
  refs.drawerMaxFails?.addEventListener("input", () =>
    saveSpreadGenerationOverride("max_recursive_fails", parseNumberInput(refs.drawerMaxFails.value))
  );
  refs.drawerPromptStrategy?.addEventListener("change", () => saveSpreadGenerationOverride("prompt_adjustment_strategy", refs.drawerPromptStrategy.value));
  refs.drawerAllowUpdates?.addEventListener("change", () => saveSpreadGenerationOverride("allow_prompt_updates", refs.drawerAllowUpdates.checked));
  refs.clearJudgeOverridesBtn?.addEventListener("click", () => clearGenerationOverrides());

  refs.judgeModel?.addEventListener("change", () => saveSpreadGenerationOverride("judge_model", refs.judgeModel.value));
  refs.judgeThreshold?.addEventListener("input", () =>
    saveSpreadGenerationOverride("judge_threshold", presetToThreshold(refs.judgeThreshold.value))
  );
  refs.maxFails?.addEventListener("input", () =>
    saveSpreadGenerationOverride("max_recursive_fails", parseNumberInput(refs.maxFails.value))
  );
  refs.promptStrategy?.addEventListener("change", () => saveSpreadGenerationOverride("prompt_adjustment_strategy", refs.promptStrategy.value));
  refs.allowUpdates?.addEventListener("change", () => saveSpreadGenerationOverride("allow_prompt_updates", refs.allowUpdates.checked));

  refs.generateSpreadSelect.addEventListener("change", () => selectSpread(refs.generateSpreadSelect.value));
  [refs.generatePrompt, refs.generateNegative, refs.generateSeed].forEach((input) => {
    input.addEventListener("input", () => saveSpreadFieldsFromForm());
  });

  document.getElementById("runGeneratorBtn").addEventListener("click", runGenerator);
  refs.abortGeneratorBtn?.addEventListener("click", abortGenerator);
  document.getElementById("generateReset").addEventListener("click", () => {
    loadGenerationConfig();
    loadGenerationForm({ useOverrides: false });
  });
  document.getElementById("clearAssignmentBtn").addEventListener("click", () => clearAssignment());
  document.getElementById("addAssetBtn").addEventListener("click", createPlaceholderAsset);
  document.getElementById("manuscriptUpload")?.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await handleManuscriptUpload(file);
    event.target.value = "";
  });
  document.getElementById("manuscriptAddLinkBtn")?.addEventListener("click", handleManuscriptLinkSave);
  document.getElementById("manuscriptAddTextBtn")?.addEventListener("click", handleManuscriptTextSave);
  refs.saveManuscriptConfigBtn?.addEventListener("click", saveManuscriptGenerationConfig);
  refs.generateManuscriptBtn?.addEventListener("click", generateManuscriptFromSources);
  [
    refs.manuscriptProvider,
    refs.manuscriptOpenAIModel,
    refs.manuscriptLocalModel,
    refs.manuscriptUseEnvKey,
    refs.manuscriptApiKey,
  ].forEach((control) => {
    const updateManuscriptGenerationControls = () => {
      updateManuscriptProviderLocks();
      renderManuscriptGenerationSummary();
    };
    control?.addEventListener("input", updateManuscriptGenerationControls);
    control?.addEventListener("change", updateManuscriptGenerationControls);
  });
  const handleReferenceToggle = async (event) => {
    const button = event.target.closest("button[data-reference-id]");
    if (!button || !activeSpreadId) return;
    const refId = button.dataset.referenceId;
    const spread = spreads.find((item) => item.spread_id === activeSpreadId);
    if (!spread) return;
    const current = Array.isArray(spread.reference_images) ? spread.reference_images : [];
    const next = current.some((item) => item.id === refId)
      ? current.filter((item) => item.id !== refId)
      : [...current, referenceInboxItems.find((item) => item.id === refId)].filter(Boolean);
    spread.reference_images = next;
    renderSpreadReferences(spread);
    renderReferenceInbox(spread);
    await saveSpreadField("reference_images", next, true);
  };
  refs.referenceInbox?.addEventListener("click", handleReferenceToggle);
  refs.spreadReferences?.addEventListener("click", handleReferenceToggle);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && projectPickerOpen) {
      closeProjectPicker();
    }
    if (event.key === "Escape" && refs.fullscreen.classList.contains("visible")) {
      closeFullscreen();
      return;
    }
    if (!refs.fullscreen.classList.contains("visible")) return;
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const currentIndex = spreads.findIndex((item) => item.spread_id === activeSpreadId);
    if (currentIndex === -1 || spreads.length === 0) return;
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const nextIndex = (currentIndex + direction + spreads.length) % spreads.length;
    selectSpread(spreads[nextIndex].spread_id);
  });

  refs.manuscriptPromptCards?.addEventListener("change", async (event) => {
    const target = event.target.closest("[data-manuscript-field]");
    if (!target) return;
    const spreadId = target.dataset.spreadId;
    const field = target.dataset.manuscriptField;
    if (!spreadId || !field) return;
    const card = target.closest(".prompt-card");
    if (card?.dataset.planningLocked === "true" && MANUSCRIPT_ILLUSTRATION_FIELDS.has(field)) {
      await refreshManuscriptData();
      return;
    }
    const value =
      target.type === "checkbox"
        ? target.checked
        : field === "visual_focus"
          ? target.value
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean)
          : target.value;
    await saveManuscriptPromptField(spreadId, field, value);
  });
  refs.manuscriptPromptCards?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manuscript-lock-toggle]");
    if (!button) return;
    const spreadId = button.dataset.spreadId;
    if (!spreadId) return;
    const locked = button.dataset.locked === "true";
    button.disabled = true;
    await saveManuscriptPromptField(spreadId, "illustration_planning_locked", !locked);
  });
}

function showTab(name, options = {}) {
  refs.tabButtons.forEach((button) => {
    const isActive = button.dataset.tab === name;
    button.classList.toggle("active", isActive);
    button.classList.toggle("secondary", !isActive);
  });
  refs.layoutView.classList.toggle("active", name === "layout");
  refs.layoutView.classList.toggle("hidden", name !== "layout");
  refs.generateView.classList.toggle("active", name === "generate");
  refs.generateView.classList.toggle("hidden", name !== "generate");
  refs.assetsView.classList.toggle("active", name === "assets");
  refs.assetsView.classList.toggle("hidden", name !== "assets");
  refs.manuscriptView.classList.toggle("active", name === "manuscript");
  refs.manuscriptView.classList.toggle("hidden", name !== "manuscript");
  if (options.persist !== false) {
    saveActiveTabPreference(name);
  }
}

async function refreshData() {
  spreads = await fetchJson(`/api/spreads?project_id=${encodeURIComponent(currentProjectId)}`);
  const assetResponse = await fetchJson(`/api/assets?project_id=${encodeURIComponent(currentProjectId)}`);
  if (Array.isArray(assetResponse)) {
    assets = assetResponse;
  } else if (assetResponse?.items && Array.isArray(assetResponse.items)) {
    assets = assetResponse.items;
  } else {
    assets = [];
  }
  generationConfig = await fetchJson("/api/config/generation");
  if (!activeSpreadId && spreads.length) {
    activeSpreadId = spreads[0].spread_id;
  }
  renderGrid();
  populateAssetSelect();
  populateGenerateSelect();
  renderAssetsView();
  if (activeSpreadId) {
    selectSpread(activeSpreadId, { skipRender: true });
  }
  loadGenerationConfig();
  populateJudgeModelSelect(refs.drawerJudgeModel, {
    selected: refs.drawerJudgeModel?.value || generationConfig.judge_model || "",
    includeBlank: false,
  });
}

async function refreshOllamaModels() {
  const response = await fetchJson("/api/ollama/models");
  ollamaModels = Array.isArray(response?.items) ? response.items : [];
  populateJudgeModelSelect(refs.drawerJudgeModel, {
    selected: refs.drawerJudgeModel?.value || generationConfig.judge_model || "",
    includeBlank: false,
  });
  populateJudgeModelSelect(refs.judgeModel, {
    selected: refs.judgeModel?.value || generationConfig.judge_model || "",
    includeBlank: false,
  });
  if (activeSpreadId) {
    const spread = spreads.find((item) => item.spread_id === activeSpreadId);
    if (spread) {
      applySpreadOverridesToDrawer(spread);
      applySpreadOverridesToGenerationForm(spread, true);
    }
  } else {
    loadGenerationConfig();
  }
  populateManuscriptLocalModelSelect(refs.manuscriptLocalModel?.value || manuscriptGenerationConfig?.local_model || "");
  updateManuscriptProviderLocks();
  await refreshSetupStatus();
}

async function refreshSetupStatus() {
  setupStatus = await fetchJson("/api/setup-status");
  renderSetupStatus();
}

function renderSetupStatus() {
  if (!refs.setupStatusSummary || !refs.setupStatusModels || !refs.setupStatusPaths || !refs.setupStatusMeta || !refs.setupStatusBadge) {
    return;
  }
  const failures = Array.isArray(setupStatus?.failures) ? setupStatus.failures : [];
  const warnings = Array.isArray(setupStatus?.warnings) ? setupStatus.warnings : [];
  const models = Array.isArray(setupStatus?.models) ? setupStatus.models : [];
  const paths = Array.isArray(setupStatus?.paths) ? setupStatus.paths : [];
  const badgeTone = failures.length ? "needs-attention" : warnings.length ? "warning" : "ready";
  const badgeLabel = failures.length ? "Needs attention" : warnings.length ? "Check warnings" : "Ready";

  refs.setupStatusBadge.textContent = badgeLabel;
  refs.setupStatusBadge.className = `setup-status-badge ${badgeTone}`;
  refs.setupStatusSummary.textContent = setupStatus?.summary || "Setup status unavailable.";

  refs.setupStatusModels.innerHTML = models.length
    ? models
        .map(
          (item) => `
            <li class="setup-status-item ${item.status || ""}">
              <span class="setup-item-main">
                <strong class="setup-item-title">${escapeHtml(item.name)}</strong>
                <span class="setup-item-tag">${escapeHtml(compactSetupRole(item.role || ""))}</span>
              </span>
              <span class="setup-item-detail">${escapeHtml(compactSetupDetail(item.detail || ""))}</span>
            </li>
          `
        )
        .join("\n")
    : `<li class="setup-status-item"><span class="setup-item-detail">No model requirements were found.</span></li>`;

  const highlightedPaths = paths.filter((item) => item.status !== "ready").slice(0, 5);
  const renderedPaths = highlightedPaths.length ? highlightedPaths : paths.slice(0, 4);
  refs.setupStatusPaths.innerHTML = renderedPaths.length
    ? renderedPaths
        .map(
          (item) => `
            <li class="setup-status-item ${item.status || ""}">
              <span class="setup-item-main">
                <strong class="setup-item-title">${escapeHtml(shortPathLabel(item.path || ""))}</strong>
              </span>
              <span class="setup-item-detail">${escapeHtml(compactSetupDetail(item.detail || ""))}</span>
            </li>
          `
        )
        .join("\n")
    : `<li class="setup-status-item"><span class="setup-item-detail">No path checks were returned.</span></li>`;

  const checkedAt = setupStatus?.checked_at ? new Date(setupStatus.checked_at).toLocaleString() : "";
  const doctorCommand = setupStatus?.doctor_command || "";
  refs.setupStatusMeta.textContent = doctorCommand
    ? `Doctor: ${compactDoctorCommand(doctorCommand)}${checkedAt ? ` • ${checkedAt}` : ""}`
    : checkedAt
      ? `Checked ${checkedAt}`
      : "";
}

function compactSetupRole(value) {
  const map = {
    image_generation: "Generator",
    local_review: "Review",
    prompt_rewrite: "Rewrite",
  };
  return map[value] || value.replaceAll("_", " ");
}

function compactSetupDetail(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  if (text === "Installed locally.") return "Installed";
  if (text === "Available.") return "OK";
  if (text === "File present.") return "Present";
  if (text.startsWith("Install with")) return "Missing";
  if (text.startsWith("Ollama check failed:")) return "Ollama check failed";
  if (text === "Path exists but is not writable by the current process.") return "Not writable here";
  return text;
}

function compactDoctorCommand(value) {
  const text = String(value || "").trim();
  const match = text.match(/^python3\s+(.+)$/);
  if (!match) return text;
  return `python3 ${shortPathLabel(match[1])}`;
}

async function refreshProjects() {
  const payload = await fetchJson("/api/projects");
  availableProjects = payload.projects || [];
  currentProjectId = payload.current?.project_id || "";
  if (refs.projectSelect) {
    refs.projectSelect.innerHTML = availableProjects
      .map((project) => `<option value="${project.id}">${project.label}</option>`)
      .concat(`<option value="${NEW_PROJECT_VALUE}">+ New project...</option>`)
      .join("\n");
    refs.projectSelect.value = currentProjectId;
  }
  renderProjectPicker();
}

function renderProjectPicker() {
  if (!refs.projectSelectLabel || !refs.projectSelectMenu) return;
  const current = availableProjects.find((project) => project.id === currentProjectId);
  refs.projectSelectLabel.textContent = current?.label || "Choose project";
  refs.projectSelectMenu.innerHTML = availableProjects
    .map((project) => {
      const active = project.id === currentProjectId;
      return `
        <button
          class="project-menu-option ${active ? "active" : ""}"
          type="button"
          role="option"
          aria-selected="${active ? "true" : "false"}"
          data-project-id="${project.id}"
        >
          <span class="project-menu-main">${escapeHtml(project.label)}</span>
          <span class="project-menu-meta">${escapeHtml(project.mode === "overnight" ? "Magic Book" : project.source === "custom" ? "Custom" : "Built-in")}</span>
        </button>
      `;
    })
    .concat(
      `
        <button class="project-menu-option project-menu-create" type="button" role="option" aria-selected="false" data-project-id="${NEW_PROJECT_VALUE}">
          <span class="project-menu-main">+ New project...</span>
          <span class="project-menu-meta">Magic Book</span>
        </button>
      `
    )
    .join("\n");
}

function toggleProjectPicker(force) {
  const next = typeof force === "boolean" ? force : !projectPickerOpen;
  projectPickerOpen = next;
  refs.projectSelectMenu?.classList.toggle("hidden", !next);
  refs.projectSelectButton?.setAttribute("aria-expanded", next ? "true" : "false");
  refs.projectSelectShell?.classList.toggle("open", next);
}

function closeProjectPicker() {
  toggleProjectPicker(false);
}

function toggleProjectModal(open) {
  if (!refs.projectModal) return;
  refs.projectModal.classList.toggle("hidden", !open);
  refs.projectModal.setAttribute("aria-hidden", open ? "false" : "true");
  updateMagicBookModalState(lastStatus);
  if (open) {
    refs.newProjectTitle?.focus();
  }
}

async function createMagicProject() {
  const title = refs.newProjectTitle?.value?.trim() || "";
  const story = refs.newProjectStory?.value?.trim() || "";
  const overnight = Boolean(refs.newProjectOvernight?.checked);
  if (lastStatus?.running) {
    if (refs.newProjectStatus) {
      refs.newProjectStatus.textContent = `A workflow is already running: ${lastStatus.status || "please wait for it to finish."}`;
    }
    updateMagicBookModalState(lastStatus);
    return;
  }
  if (!story) {
    if (refs.newProjectStatus) {
      refs.newProjectStatus.textContent = "Add a short story brief first, or use Load tiny test.";
    }
    return;
  }
  if (refs.newProjectStatus) {
    refs.newProjectStatus.textContent = "Starting one-button Magic Book pipeline...";
  }
  const response = await fetch("/api/projects/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      story,
      overnight_mode: overnight,
    }),
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.newProjectStatus.textContent = body.error || "Could not create the project.";
    return;
  }
  refs.newProjectStatus.textContent = body.message || "Magic book started.";
  await refreshProjects();
  updateMagicBookModalState({ ...lastStatus, running: true, status: body.message || "Magic book started." });
}

function loadTinyMagicBookTest() {
  if (refs.newProjectTitle) {
    refs.newProjectTitle.value = TINY_MAGIC_BOOK_TEST.title;
  }
  if (refs.newProjectStory) {
    refs.newProjectStory.value = TINY_MAGIC_BOOK_TEST.story;
  }
  if (refs.newProjectOvernight) {
    refs.newProjectOvernight.checked = true;
  }
  if (refs.newProjectStatus) {
    refs.newProjectStatus.textContent = "Tiny overnight test loaded. Start magic book to generate the full chain.";
  }
}

function isMagicBookStatus(statusText) {
  const text = String(statusText || "").toLowerCase();
  return text.includes("magic book");
}

function parseMagicBookProgress(statusText, running, hasError) {
  const text = String(statusText || "").toLowerCase();
  const renderMatch = text.match(/rendering spread\s+(\d+)\s+of\s+(\d+)/);
  const renderMeta = renderMatch ? `Spread ${renderMatch[1]} of ${renderMatch[2]}` : "";
  const steps = [
    { key: "story", label: "Draft source story", meta: "Turn the brief into a fuller source draft.", state: "upcoming" },
    { key: "plan", label: "Plan spreads and prompts", meta: "Build manuscript text, spread beats, and image prompts.", state: "upcoming" },
    { key: "render", label: "Render the book", meta: renderMeta || "Run image generation and recursive review spread by spread.", state: "upcoming" },
  ];

  if (!text || (!running && !hasError && !isMagicBookStatus(statusText))) {
    return steps;
  }

  if (text.includes("drafting source story")) {
    steps[0].state = hasError ? "error" : running ? "current" : "done";
    return steps;
  }

  if (text.includes("planning spreads")) {
    steps[0].state = "done";
    steps[1].state = hasError ? "error" : running ? "current" : "done";
    return steps;
  }

  if (text.includes("rendering spread")) {
    steps[0].state = "done";
    steps[1].state = "done";
    steps[2].state = hasError ? "error" : running ? "current" : "done";
    return steps;
  }

  if (text.includes("finished") || text.includes("ready")) {
    steps.forEach((step) => {
      step.state = "done";
    });
    return steps;
  }

  if (hasError) {
    const currentIndex = text.includes("planning") ? 1 : text.includes("render") ? 2 : 0;
    for (let index = 0; index < currentIndex; index += 1) {
      steps[index].state = "done";
    }
    steps[currentIndex].state = "error";
  }

  return steps;
}

function renderMagicBookSteps(steps) {
  if (!refs.magicBookSteps) return;
  refs.magicBookSteps.innerHTML = (steps || [])
    .map(
      (step) => `
        <li class="magic-book-step ${step.state || "upcoming"}">
          <span>
            <span class="magic-book-step-label">${escapeHtml(step.label || "")}</span>
            <span class="magic-book-step-meta">${escapeHtml(step.meta || "")}</span>
          </span>
        </li>
      `
    )
    .join("\n");
}

function updateMagicBookModalState(state) {
  if (!refs.magicBookProgressBadge || !refs.magicBookProgressText || !refs.magicBookProgressHint || !refs.createProjectBtn) {
    return;
  }
  const running = Boolean(state?.running);
  const statusText = String(state?.status || "").trim();
  const errorText = String(state?.last_error || "").trim();
  const magicBookActive = isMagicBookStatus(statusText);
  const steps = parseMagicBookProgress(statusText, running, Boolean(errorText));

  let badge = "Idle";
  let badgeClass = "idle";
  let summary = "No Magic Book run is active yet.";
  let hint = "Start a Magic Book run here and keep this modal open to watch the pipeline move through story drafting, spread planning, and rendering.";

  if (running && magicBookActive) {
    badge = "Running";
    badgeClass = "running";
    summary = statusText;
    hint = "Magic Book is actively moving through the overnight pipeline. You can leave this modal open and watch it update.";
  } else if (running) {
    badge = "Busy";
    badgeClass = "running";
    summary = statusText || "Another generation workflow is currently running.";
    hint = "Magic Book can only start when the current workflow finishes.";
  } else if (errorText && magicBookActive) {
    badge = "Error";
    badgeClass = "error";
    summary = statusText || "Magic Book failed.";
    hint = errorText;
  } else if (statusText && magicBookActive) {
    badge = "Complete";
    badgeClass = "complete";
    summary = statusText;
    hint = "This Magic Book run has stopped. You can switch to the project, inspect spreads, or start another test.";
  }

  refs.magicBookProgressBadge.textContent = badge;
  refs.magicBookProgressBadge.className = `magic-book-progress-badge ${badgeClass}`;
  refs.magicBookProgressText.textContent = summary;
  renderMagicBookSteps(steps);
  refs.magicBookProgressHint.textContent = hint;
  refs.createProjectBtn.disabled = running;
  refs.loadTinyMagicBookBtn && (refs.loadTinyMagicBookBtn.disabled = running);
}

async function refreshReferenceInbox() {
  const payload = await fetchJson("/api/references");
  referenceInboxItems = payload.items || [];
}

async function refreshManuscriptData() {
  manuscriptData = await fetchJson(`/api/manuscript?project_id=${encodeURIComponent(currentProjectId || "")}`);
  manuscriptGenerationConfig = manuscriptData?.generation?.config || manuscriptGenerationConfig;
  manuscriptGenerationStatus = manuscriptData?.generation?.status || manuscriptGenerationStatus;
  if (!activeManuscriptDocId && manuscriptData.documents?.length) {
    activeManuscriptDocId = manuscriptData.documents[0].id;
  }
  if (activeManuscriptDocId && !manuscriptData.documents.some((doc) => doc.id === activeManuscriptDocId)) {
    activeManuscriptDocId = manuscriptData.documents[0]?.id || "";
  }
  if (manuscriptDocEditing) {
    const activeDoc = manuscriptData.documents.find((doc) => doc.id === activeManuscriptDocId);
    manuscriptDocDraft = activeDoc?.content || manuscriptDocDraft;
  }
  renderManuscriptView();
}

function renderManuscriptView() {
  renderManuscriptDocs();
  renderPromptCards();
  renderSourceFiles();
  renderManuscriptGenerationPanel();
}

function renderManuscriptDocs() {
  if (!refs.manuscriptDocTabs || !refs.manuscriptDocTitle || !refs.manuscriptDocBody || !refs.manuscriptDocActions) return;
  const docs = (manuscriptData.documents || []).filter((doc) => ["manuscript", "dummy-layout"].includes(doc.id));
  refs.manuscriptDocTabs.innerHTML = docs
    .map(
      (doc) => `
        <button class="ghost-btn manuscript-doc-tab ${doc.id === activeManuscriptDocId ? "active" : ""} ${manuscriptDocTabClass(doc.id)}" type="button" data-doc-id="${doc.id}">
          ${escapeHtml(doc.label)}
        </button>
      `
    )
    .join("\n");
  const activeDoc = docs.find((doc) => doc.id === activeManuscriptDocId) || docs[0];
  const content = activeDoc?.content || "No manuscript document loaded for this project yet.";
  refs.manuscriptDocTitle.textContent = activeDoc?.label || "Select a document";
  refs.manuscriptDocHelper.textContent = manuscriptDocEditing
    ? "Editing is unlocked for this file. Save writes directly back to the project manuscript folder."
    : manuscriptDocHelperText(activeDoc?.id || "");
  refs.manuscriptDocBody.textContent = content;
  refs.manuscriptDocBody.classList.toggle("hidden", manuscriptDocEditing);
  refs.manuscriptDocEditor.classList.toggle("hidden", !manuscriptDocEditing);
  refs.manuscriptDocEditor.value = manuscriptDocEditing ? manuscriptDocDraft : content;
  refs.manuscriptDocStatus.textContent = manuscriptDocEditing ? "Editing unlocked." : "";
  refs.manuscriptDocActions.innerHTML = activeDoc
    ? manuscriptDocEditing
      ? `
          <button class="ghost-btn" type="button" data-manuscript-doc-action="cancel">Cancel</button>
          <button class="primary-btn" type="button" data-manuscript-doc-action="save">Save</button>
        `
      : `
          ${activeDoc.id === "dummy-layout" ? `<button class="ghost-btn" type="button" data-manuscript-doc-action="sync">Sync to spreads</button>` : ""}
          <button class="ghost-btn" type="button" data-manuscript-doc-action="edit">Edit</button>
        `
    : "";
  refs.manuscriptDocTabs.querySelectorAll("[data-doc-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const nextDocId = button.dataset.docId || "";
      if (!canSwitchManuscriptDoc(nextDocId)) return;
      activeManuscriptDocId = nextDocId;
      renderManuscriptDocs();
    });
  });
  refs.manuscriptDocActions.querySelectorAll("[data-manuscript-doc-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.manuscriptDocAction;
      if (action === "edit") {
        manuscriptDocEditing = true;
        manuscriptDocDraft = activeDoc?.content || "";
        renderManuscriptDocs();
        refs.manuscriptDocEditor?.focus();
        refs.manuscriptDocEditor?.setSelectionRange?.(0, 0);
        return;
      }
      if (action === "cancel") {
        manuscriptDocEditing = false;
        manuscriptDocDraft = "";
        refs.manuscriptDocStatus.textContent = "Changes discarded.";
        renderManuscriptDocs();
        return;
      }
      if (action === "save") {
        await saveManuscriptDocument();
        return;
      }
      if (action === "sync") {
        await syncManuscriptToSpreads();
      }
    });
  });
  refs.manuscriptDocEditor.oninput = () => {
    manuscriptDocDraft = refs.manuscriptDocEditor.value;
  };
}

function manuscriptDocTabClass(docId) {
  return docId === "manuscript" || docId === "dummy-layout" ? "primary" : "secondary";
}

function manuscriptDocHelperText(docId) {
  if (docId === "dummy-layout") {
    return "This is the spread blueprint used by Layout and Generate. Edit it, then sync to spreads.";
  }
  if (docId === "manuscript") {
    return "This is the main story draft. Use Dummy Layout to shape the spread text that feeds Layout and Generate.";
  }
  return "Locked by default. Use Edit to make changes to this manuscript file.";
}

function canSwitchManuscriptDoc(nextDocId) {
  if (!manuscriptDocEditing || nextDocId === activeManuscriptDocId) return true;
  const activeDoc = (manuscriptData.documents || []).find((doc) => doc.id === activeManuscriptDocId);
  const unchanged = manuscriptDocDraft === (activeDoc?.content || "");
  if (unchanged) {
    manuscriptDocEditing = false;
    manuscriptDocDraft = "";
    return true;
  }
  const discard = window.confirm("Discard unsaved manuscript edits?");
  if (discard) {
    manuscriptDocEditing = false;
    manuscriptDocDraft = "";
  }
  return discard;
}

async function saveManuscriptDocument() {
  const activeDoc = (manuscriptData.documents || []).find((doc) => doc.id === activeManuscriptDocId);
  if (!activeDoc) return;
  const content = refs.manuscriptDocEditor?.value ?? manuscriptDocDraft;
  refs.manuscriptDocStatus.textContent = `Saving ${activeDoc.label}...`;
  const response = await fetch("/api/manuscript/document", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: currentProjectId || "",
      filename: activeDoc.filename,
      content,
    }),
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.manuscriptDocStatus.textContent = body.error || "Save failed.";
    return;
  }
  manuscriptDocEditing = false;
  manuscriptDocDraft = "";
  refs.manuscriptDocStatus.textContent = body.message || "Saved manuscript file.";
  await refreshManuscriptData();
}

async function syncManuscriptToSpreads() {
  if (!currentProjectId) return;
  refs.manuscriptDocStatus.textContent = "Syncing dummy layout into spreads...";
  const response = await fetch("/api/projects/load", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: currentProjectId }),
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.manuscriptDocStatus.textContent = body.error || "Sync failed.";
    return;
  }
  await refreshProjects();
  await refreshData();
  await refreshManuscriptData();
  refs.manuscriptDocStatus.textContent = body.message || "Spread data refreshed from dummy layout.";
}

function renderPromptCards() {
  if (!refs.manuscriptPromptCards) return;
  const prompts = manuscriptData.prompts || [];
  refs.manuscriptPromptCards.innerHTML = prompts
    .map(
      (item) => {
        const planningLocked = Boolean(item.illustration_planning_locked);
        return `
        <article class="prompt-card ${planningLocked ? "prompt-card-locked" : ""}" data-planning-locked="${planningLocked ? "true" : "false"}">
          <div class="prompt-card-header">
            <strong>${escapeHtml(item.title)}</strong>
            <span>${escapeHtml(item.pages || "")}</span>
          </div>
          <div class="prompt-card-block">
            <span class="prompt-card-label">Spread text</span>
            <p class="prompt-card-story">${escapeHtml(item.story_text || "")}</p>
          </div>
          <div class="prompt-card-block">
            <div class="prompt-card-label-row">
              <span class="prompt-card-label">Image prompt</span>
              <button
                class="prompt-card-lock-btn ${planningLocked ? "locked" : ""}"
                type="button"
                data-manuscript-lock-toggle="illustration"
                data-spread-id="${escapeHtml(item.spread_id)}"
                data-locked="${planningLocked ? "true" : "false"}"
                aria-pressed="${planningLocked ? "true" : "false"}"
              >${planningLocked ? "Unlock planning" : "Lock planning"}</button>
            </div>
            <textarea rows="4" data-manuscript-field="prompt" data-spread-id="${escapeHtml(item.spread_id)}" ${planningLocked ? "disabled" : ""}>${escapeHtml(
              item.prompt || ""
            )}</textarea>
          </div>
          ${
            item.warnings?.length
              ? `<div class="prompt-card-warnings">
                  ${item.warnings.map((warning) => `<p>${escapeHtml(warning)}</p>`).join("")}
                </div>`
              : ""
          }
          <details class="prompt-card-advanced">
            <summary>Advanced planning</summary>
            <div class="prompt-card-advanced-body">
              <div class="prompt-card-form-grid">
                <label>
                  <span class="prompt-card-label">Story role</span>
                  <select data-manuscript-field="story_role" data-spread-id="${escapeHtml(item.spread_id)}" ${planningLocked ? "disabled" : ""}>
                    ${renderSelectOptions(STORY_ROLE_OPTIONS, item.story_role)}
                  </select>
                </label>
                <label>
                  <span class="prompt-card-label">Beat type</span>
                  <select data-manuscript-field="beat_type" data-spread-id="${escapeHtml(item.spread_id)}" ${planningLocked ? "disabled" : ""}>
                    ${renderSelectOptions(BEAT_TYPE_OPTIONS, item.beat_type)}
                  </select>
                </label>
              </div>
              <div class="prompt-card-block">
              <span class="prompt-card-label">What this spread needs to do</span>
                <textarea rows="2" data-manuscript-field="spread_intent" data-spread-id="${escapeHtml(item.spread_id)}" ${planningLocked ? "disabled" : ""}>${escapeHtml(
                  item.spread_intent || ""
                )}</textarea>
              </div>
              <div class="prompt-card-form-grid">
                <label>
                  <span class="prompt-card-label">Emotional state</span>
                  <textarea rows="2" data-manuscript-field="emotional_state" data-spread-id="${escapeHtml(item.spread_id)}" ${planningLocked ? "disabled" : ""}>${escapeHtml(
                    item.emotional_state || ""
                  )}</textarea>
                </label>
                <label>
                  <span class="prompt-card-label">Visual focus</span>
                  <textarea rows="2" data-manuscript-field="visual_focus" data-spread-id="${escapeHtml(item.spread_id)}" ${planningLocked ? "disabled" : ""}>${escapeHtml(
                    (item.visual_focus || []).join(", ")
                  )}</textarea>
                </label>
              </div>
              <label class="prompt-card-checkbox">
                <input
                  type="checkbox"
                  data-manuscript-field="page_turn_tension"
                  data-spread-id="${escapeHtml(item.spread_id)}"
                  ${item.page_turn_tension ? "checked" : ""}
                  ${planningLocked ? "disabled" : ""}
                />
                <span>
                  <span class="prompt-card-label">Page-turn tension</span>
                  <small>Use this when the spread ends on an unresolved beat or reveal.</small>
                </span>
              </label>
              <div class="prompt-card-block">
                <span class="prompt-card-label">Illustration notes</span>
                <textarea rows="3" data-manuscript-field="illustration_notes" data-spread-id="${escapeHtml(item.spread_id)}" ${planningLocked ? "disabled" : ""}>${escapeHtml(
                  item.illustration_notes || item.note || ""
                )}</textarea>
              </div>
            </div>
          </details>
        </article>
      `;
      }
    )
    .join("\n");
}

function renderSelectOptions(options, selectedValue) {
  return options
    .map((value) => {
      const label = value
        ? value
            .split("_")
            .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
            .join(" ")
        : "Not set";
      return `<option value="${escapeHtml(value)}" ${value === selectedValue ? "selected" : ""}>${escapeHtml(label)}</option>`;
    })
    .join("");
}

function renderSourceFiles() {
  if (!refs.manuscriptSourceList) return;
  const items = manuscriptData.sources || [];
  refs.manuscriptSourceList.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <article class="manuscript-source-card">
              <div class="manuscript-source-meta">
                <strong>${escapeHtml(item.label)}</strong>
                <span>${escapeHtml((item.kind || "").toUpperCase())}</span>
              </div>
              ${item.preview ? `<pre>${escapeHtml(item.preview)}</pre>` : `<p class="muted">Preview unavailable. Open the source file directly.</p>`}
              <a class="asset-link" href="${item.url}" target="_blank" rel="noreferrer">${String(item.kind || "").includes("link") || item.kind === "youtube" ? "Open link" : "Open source"}</a>
            </article>
          `
        )
        .join("\n")
    : `<p class="muted">No uploaded source material yet. Add a PDF or text file to keep it with this project.</p>`;
}

function renderManuscriptGenerationPanel() {
  if (!manuscriptGenerationConfig) return;
  refs.manuscriptProvider && (refs.manuscriptProvider.value = manuscriptGenerationConfig.provider || "openai");
  refs.manuscriptOpenAIModel && (refs.manuscriptOpenAIModel.value = manuscriptGenerationConfig.openai_model || "gpt-5.2");
  populateManuscriptLocalModelSelect(manuscriptGenerationConfig.local_model || "");
  refs.manuscriptUseEnvKey && (refs.manuscriptUseEnvKey.checked = Boolean(manuscriptGenerationConfig.use_env_api_key));
  refs.manuscriptApiKey && (refs.manuscriptApiKey.value = manuscriptGenerationConfig.api_key || "");
  updateManuscriptProviderLocks();
  renderManuscriptGenerationSummary();
  if (refs.manuscriptGenerationStatus) {
    refs.manuscriptGenerationStatus.textContent = manuscriptGenerationStatus?.status || "Ready.";
  }
}

function renderManuscriptGenerationSummary() {
  if (!refs.manuscriptGenerationSummary) return;
  const provider = refs.manuscriptProvider?.value || manuscriptGenerationConfig?.provider || "openai";
  const openaiModel = refs.manuscriptOpenAIModel?.value?.trim() || "gpt-5.2";
  const localModel = refs.manuscriptLocalModel?.value?.trim() || "llama3.2:3b";
  const useEnv = Boolean(refs.manuscriptUseEnvKey?.checked);
  const hasApiKey = Boolean(refs.manuscriptApiKey?.value?.trim());
  if (refs.manuscriptProviderBadge) {
    refs.manuscriptProviderBadge.textContent = provider === "openai" ? "OPENAI" : "OLLAMA";
  }
  refs.manuscriptGenerationSummary.textContent =
    provider === "openai"
      ? `OpenAI will use ${openaiModel}. API key source: ${hasApiKey ? "saved in this dashboard" : useEnv ? "OPENAI_API_KEY environment variable" : "missing until you add one"}.`
      : `Local generation will use ${localModel} through Ollama.`;
}

function populateManuscriptLocalModelSelect(selected = "") {
  if (!refs.manuscriptLocalModel) return;
  const requested = selected || manuscriptGenerationConfig?.local_model || "llama3.2:3b";
  const seen = new Set();
  const options = [];
  if (requested && !ollamaModels.some((item) => item.name === requested)) {
    options.push({ value: requested, label: `${requested} (saved)` });
    seen.add(requested);
  }
  ollamaModels.forEach((item) => {
    if (!item?.name || seen.has(item.name)) return;
    options.push({ value: item.name, label: item.name });
    seen.add(item.name);
  });
  if (!options.length) {
    options.push({ value: requested || "llama3.2:3b", label: requested || "llama3.2:3b" });
  }
  refs.manuscriptLocalModel.innerHTML = options
    .map((item) => `<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`)
    .join("\n");
  refs.manuscriptLocalModel.value = requested || options[0].value;
}

function updateManuscriptProviderLocks() {
  const provider = refs.manuscriptProvider?.value || "openai";
  const openaiActive = provider === "openai";
  if (refs.manuscriptOpenAIModel) {
    refs.manuscriptOpenAIModel.disabled = !openaiActive;
  }
  if (refs.manuscriptUseEnvKey) {
    refs.manuscriptUseEnvKey.disabled = !openaiActive;
  }
  if (refs.manuscriptApiKey) {
    refs.manuscriptApiKey.disabled = !openaiActive;
  }
  if (refs.manuscriptLocalModel) {
    refs.manuscriptLocalModel.disabled = openaiActive;
  }
}

async function handleManuscriptUpload(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("project_id", currentProjectId || "");
  refs.manuscriptUploadStatus.textContent = `Uploading ${file.name}...`;
  const response = await fetch("/api/manuscript/upload", {
    method: "POST",
    body: formData,
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.manuscriptUploadStatus.textContent = body.error || "Source upload failed.";
    return;
  }
  refs.manuscriptUploadStatus.textContent = body.message || `Uploaded ${file.name}.`;
  await refreshManuscriptData();
}

async function handleManuscriptLinkSave() {
  const url = refs.manuscriptSourceLink?.value?.trim();
  if (!url) return;
  refs.manuscriptUploadStatus.textContent = "Saving link...";
  const response = await fetch("/api/manuscript/link", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: currentProjectId || "", url }),
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.manuscriptUploadStatus.textContent = body.error || "Link save failed.";
    return;
  }
  refs.manuscriptSourceLink.value = "";
  refs.manuscriptUploadStatus.textContent = body.message || "Saved link.";
  await refreshManuscriptData();
}

async function handleManuscriptTextSave() {
  const text = refs.manuscriptSourceText?.value?.trim();
  if (!text) return;
  refs.manuscriptUploadStatus.textContent = "Saving text...";
  const response = await fetch("/api/manuscript/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: currentProjectId || "", text }),
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.manuscriptUploadStatus.textContent = body.error || "Text save failed.";
    return;
  }
  refs.manuscriptSourceText.value = "";
  refs.manuscriptUploadStatus.textContent = body.message || "Saved text.";
  await refreshManuscriptData();
}

async function saveManuscriptGenerationConfig() {
  const provider = refs.manuscriptProvider?.value || "openai";
  const payload = {
    provider,
    openai_model: refs.manuscriptOpenAIModel?.value?.trim() || "gpt-5.2",
    local_model: refs.manuscriptLocalModel?.value?.trim() || "llama3.2:3b",
    use_env_api_key: provider === "openai" ? Boolean(refs.manuscriptUseEnvKey?.checked) : false,
    api_key: provider === "openai" ? refs.manuscriptApiKey?.value?.trim() || "" : "",
  };
  refs.manuscriptGenerationStatus.textContent = "Saving manuscript settings...";
  const response = await fetch("/api/manuscript/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.manuscriptGenerationStatus.textContent = body.error || "Could not save manuscript settings.";
    return false;
  }
  manuscriptGenerationConfig = body.config || payload;
  renderManuscriptGenerationPanel();
  refs.manuscriptGenerationStatus.textContent = "Manuscript settings saved.";
  return true;
}

async function generateManuscriptFromSources() {
  const saved = await saveManuscriptGenerationConfig();
  if (!saved) return;
  refs.manuscriptGenerationStatus.textContent = "Starting manuscript generation...";
  const response = await fetch("/api/manuscript/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: currentProjectId || "" }),
  });
  const body = await response.json();
  if (!response.ok || body.error) {
    refs.manuscriptGenerationStatus.textContent = body.error || "Could not start manuscript generation.";
    return;
  }
  refs.manuscriptGenerationStatus.textContent = body.message || "Manuscript generation started.";
}

async function saveManuscriptPromptField(spreadId, field, value) {
  const updated = await patchSpread(spreadId, { [field]: value });
  if (!updated) return;
  spreads = spreads.map((item) => (item.spread_id === spreadId ? updated : item));
  await refreshManuscriptData();
}

function renderGrid() {
  refs.layoutGrid.innerHTML = spreads
    .map((spread) => {
      const asset = assets.find((item) => item.asset_id === spread.assigned_image_id);
      const previewUrl = getSpreadPreviewUrl(spread, asset);
      const hasImage = Boolean(previewUrl);
      const artState = getSpreadArtState(spread, asset, hasImage);
      const previewStyle = hasImage
        ? `url(${previewUrl})`
        : fallbackPalette[spread.layout_type] || fallbackPalette.span;
      return `
        <article
          class="spread-tile layout-${spread.layout_type} ${spread.spread_id === activeSpreadId ? "active" : ""}"
          data-id="${spread.spread_id}"
          tabindex="0"
          role="button"
          aria-label="Open ${spread.title} spread"
        >
          <div class="tile-header">
            <strong>${spread.title}</strong>
            <span>${spread.left_page}–${spread.right_page}</span>
          </div>
          <div class="tile-preview" style="background-image:${previewStyle}">
            ${hasImage ? "" : "<span class=\"tile-preview-placeholder\">No art yet</span>"}
          </div>
          <p class="tile-caption">${spread.excerpt}</p>
          <div class="tile-status">
            <span class="status-${artState}">${artStateLabels[artState] || artState}</span>
            <span class="status-source">${describeSpreadArtState(artState, asset, spread)}</span>
            <span class="layout-type">${spread.layout_type}</span>
            ${hasImage ? "" : "<span class=\"tile-warning-dot\" title=\"Spread missing art\"></span>"}
          </div>
          <div class="tile-cta-row">
            <button class="ghost-btn tile-open-btn" type="button" data-action="open-spread">Open spread</button>
          </div>
        </article>
      `;
    })
    .join("\n");
}

function getSpreadArtState(spread, asset, hasImage) {
  if (!hasImage) return "draft";
  if (asset?.source_type === "project-select") return "approved";
  if (asset?.source_type === "project-raw") return "candidate";
  if (!asset && spread.assigned_image_preview?.includes("/storyboard/renders/raw/")) return "candidate";
  return "assigned";
}

function describeSpreadArtState(state, asset, spread) {
  if (state === "approved") return "selected";
  if (state === "candidate") return "raw render";
  if (state === "assigned") {
    if (asset?.source_type) return asset.source_type;
    if (spread.assigned_image_id) return "assigned asset";
    return "preview";
  }
  return "no art";
}

function selectSpread(id, options = {}) {
  if (!id) return;
  activeSpreadId = id;
  const spread = spreads.find((item) => item.spread_id === id);
  if (!spread) return;
  populateDetail(spread);
  updateTileHighlight();
  if (options.focusDrawer) {
    focusDetailDrawer();
  }
  if (!options.skipRender) {
    renderGrid();
  }
}

function focusDetailDrawer() {
  const focusTarget = document.getElementById("detailDrawer") || refs.spreadPreview;
  focusTarget?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function populateDetail(spread) {
  refs.drawerTitle.textContent = `${spread.spread_id.toUpperCase()} · Pages ${spread.left_page}–${spread.right_page}`;
  refs.fullscreenLeftTitle.textContent = `Left page · ${spread.left_page}`;
  refs.fullscreenRightTitle.textContent = `Right page · ${spread.right_page}`;
  refs.promptField.value = spread.prompt;
  refs.referenceNotesField.value = spread.reference_notes || "";
  refs.negativeField.value = spread.negative_prompt;
  refs.seedField.value = spread.seed || "";
  refs.notesField.value = spread.notes;
  refs.statusSelect.value = spread.status;
  refs.promptStatus.textContent = `Prompt: ${spread.prompt_status}`;
  refs.lastUpdated.textContent = `Last updated ${new Date(spread.last_updated_ts || Date.now()).toLocaleString()}`;
  refs.placeRadios.forEach((radio) => (radio.checked = radio.value === spread.layout_type));
  const overlay = spread.text_overlay || {};
  refs.overlayVisible.checked = overlay.visible;
  refs.overlayX.value = overlay.x ?? 5;
  refs.overlayY.value = overlay.y ?? 45;
  refs.overlayWidth.value = overlay.width ?? 60;
  refs.overlayAlignment.value = overlay.alignment || "left";
  refs.overlayWash.value = overlay.wash_opacity ?? 0.6;
  const assetPreview = assets.find((item) => item.asset_id === spread.assigned_image_id);
  applyPreview(spread, assetPreview);
  updateApproveButton(spread, assetPreview);
  updateOverlayVisual(spread);
  updateFullscreenOverlay(spread);
  renderSpreadReferences(spread);
  renderReferenceInbox(spread);
  applySpreadOverridesToDrawer(spread);
  if (refs.generateSpreadSelect) {
    refs.generateSpreadSelect.value = spread.spread_id;
  }
  loadGenerationForm();
}

function renderSpreadReferences(spread) {
  const refsForSpread = Array.isArray(spread.reference_images) ? spread.reference_images : [];
  if (!refs.spreadReferences) return;
  refs.spreadReferences.innerHTML = refsForSpread.length
    ? refsForSpread
        .map(
          (item) => `
            <article class="reference-chip-card">
              <div class="reference-thumb" style="background-image:${cssBackgroundImage(item.url)}"></div>
              <div class="reference-meta">
                <strong>${item.label}</strong>
                <button class="ghost-btn" type="button" data-reference-id="${item.id}">Remove</button>
              </div>
            </article>
          `
        )
        .join("\n")
    : `<p class="muted">No reference images attached to this spread yet.</p>`;
}

function renderReferenceInbox(spread) {
  if (!refs.referenceInbox) return;
  refs.referenceInbox.innerHTML = referenceInboxItems
    .map(
      (item) => `
        <article class="reference-inbox-card">
          <div class="reference-thumb" style="background-image:${cssBackgroundImage(item.url)}"></div>
          <div class="reference-meta">
            <strong>${item.label}</strong>
          </div>
        </article>
      `
    )
    .join("\n");
}

function applyPreview(spread, asset) {
  const fallback = fallbackPalette[spread.layout_type] || fallbackPalette.span;
  const previewUrl = getSpreadPreviewUrl(spread, asset);
  const hasImage = Boolean(previewUrl);
  const background = hasImage ? cssBackgroundImage(previewUrl) : fallback;
  const isSpan = spread.layout_type === "span";
  refs.spreadPreview?.classList.toggle("is-empty", !hasImage);
  refs.spreadPreview.style.backgroundImage = background;
  refs.fullscreenPages?.classList.toggle("span-layout", isSpan);
  refs.fullscreenPageLeft?.classList.toggle("span-layout", isSpan);
  refs.fullscreenPageRight?.classList.toggle("span-layout", isSpan);
  if (isSpan && hasImage) {
    refs.fullscreenLeft.style.backgroundImage = background;
    refs.fullscreenRight.style.backgroundImage = background;
    refs.fullscreenLeft.style.backgroundPosition = "left center";
    refs.fullscreenRight.style.backgroundPosition = "right center";
    applyFullscreenSpreadCover(previewUrl);
  } else {
    refs.fullscreenLeft.style.backgroundImage = background;
    refs.fullscreenRight.style.backgroundImage = background;
    refs.fullscreenLeft.style.backgroundSize = "";
    refs.fullscreenRight.style.backgroundSize = "";
    refs.fullscreenLeft.style.backgroundPosition = "";
    refs.fullscreenRight.style.backgroundPosition = "";
  }
  refs.dropTarget?.classList.toggle("has-image", hasImage);
  if (refs.dropTargetCopy) {
    refs.dropTargetCopy.textContent = hasImage
      ? "Drop a new image here to replace the current art."
      : "Upload or drop artwork to start the spread preview.";
  }
}

function loadImageDimensions(url) {
  if (!url) return Promise.resolve(null);
  const cached = imageDimensionCache.get(url);
  if (cached) {
    return cached instanceof Promise ? cached : Promise.resolve(cached);
  }
  const pending = new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const dims = { width: img.naturalWidth || 0, height: img.naturalHeight || 0 };
      imageDimensionCache.set(url, dims);
      resolve(dims);
    };
    img.onerror = () => {
      imageDimensionCache.delete(url);
      resolve(null);
    };
    img.src = url;
  });
  imageDimensionCache.set(url, pending);
  return pending;
}

async function applyFullscreenSpreadCover(url) {
  const left = refs.fullscreenLeft;
  const right = refs.fullscreenRight;
  if (!left || !right || !url) return;
  const dims = await loadImageDimensions(url);
  if (!dims || !dims.width || !dims.height) {
    left.style.backgroundSize = "";
    right.style.backgroundSize = "";
    return;
  }
  const activeSpread = spreads.find((item) => item.spread_id === activeSpreadId);
  if (!activeSpread || getSpreadPreviewUrl(activeSpread, assets.find((item) => item.asset_id === activeSpread.assigned_image_id)) !== url) {
    return;
  }
  const leftWidth = left.clientWidth || 1;
  const rightWidth = right.clientWidth || leftWidth;
  const halfHeight = left.clientHeight || 1;
  const totalWidth = leftWidth + rightWidth;
  const totalHeight = Math.max(halfHeight, right.clientHeight || halfHeight);
  const imageRatio = dims.width / dims.height;
  const containerRatio = totalWidth / totalHeight;

  let renderedWidth = totalWidth;
  let renderedHeight = totalHeight;
  if (imageRatio > containerRatio) {
    renderedWidth = totalHeight * imageRatio;
  } else {
    renderedHeight = totalWidth / imageRatio;
  }

  const widthPercent = (renderedWidth / leftWidth) * 100;
  const heightPercent = (renderedHeight / halfHeight) * 100;
  const sizeValue = `${widthPercent}% ${heightPercent}%`;
  left.style.backgroundSize = sizeValue;
  right.style.backgroundSize = sizeValue;
}

function getSpreadPreviewUrl(spread, asset) {
  return asset?.mirror_url || spread.assigned_image_preview || "";
}

function cssBackgroundImage(url) {
  return `url("${encodeURI(url)}")`;
}

function toggleOverlayVisibility() {
  if (!refs.overlayVisible) return;
  const spread = spreads.find((item) => item.spread_id === activeSpreadId);
  if (!spread) return;
  refs.overlayVisible.checked = !refs.overlayVisible.checked;
  const overlay = {
    ...(spread.text_overlay || {}),
    visible: refs.overlayVisible.checked,
    x: Number(refs.overlayX.value),
    y: Number(refs.overlayY.value),
    width: Number(refs.overlayWidth.value),
    alignment: refs.overlayAlignment.value,
    wash_opacity: Number(refs.overlayWash.value),
  };
  spread.text_overlay = overlay;
  updateOverlayVisual(spread);
  updateFullscreenOverlay(spread);
  saveSpreadField("text_overlay", overlay);
}

function updateOverlayVisual(spread) {
  const overlay = spread.text_overlay || {};
  const values = {
    visible: overlay.visible === undefined ? true : overlay.visible,
    x: overlay.x ?? 5,
    y: overlay.y ?? 45,
    width: overlay.width ?? 65,
    alignment: overlay.alignment || "left",
    wash_opacity: overlay.wash_opacity ?? 0.6,
  };
  refs.previewOverlay.style.opacity = "0";
  refs.previewOverlay.style.display = "none";
  refs.previewOverlay.style.left = `${values.x}%`;
  refs.previewOverlay.style.top = `${values.y}%`;
  refs.previewOverlay.style.width = `${values.width}%`;
  refs.previewOverlay.style.textAlign = values.alignment;
  refs.previewOverlay.style.backgroundColor = `rgba(255, 255, 255, ${values.wash_opacity})`;
  refs.previewOverlay.textContent = spread.text_overlay_text;
  refs.overlayTextLeft.textContent = spread.text_overlay_text;
  refs.overlayTextRight.textContent = spread.text_overlay_text;
}

function updateFullscreenOverlay(spread) {
  const overlay = spread.text_overlay || {};
  const values = {
    visible: overlay.visible === undefined ? true : overlay.visible,
    x: overlay.x ?? 5,
    y: overlay.y ?? 45,
    width: overlay.width ?? 65,
    alignment: overlay.alignment || "left",
    wash_opacity: overlay.wash_opacity ?? 0.6,
  };
  const visible = values.visible;
  const isSpan = spread.layout_type === "span";
  [refs.overlayTextLeft, refs.overlayTextRight].forEach((el) => {
    el.style.display = !isSpan && visible ? "block" : "none";
    el.style.left = `${values.x}%`;
    el.style.top = `${values.y}%`;
    el.style.width = `${values.width}%`;
    el.style.textAlign = values.alignment;
    el.style.backgroundColor = `rgba(255, 255, 255, ${values.wash_opacity})`;
    el.style.opacity = !isSpan && visible ? "1" : "0";
  });
  if (refs.fullscreenSpreadOverlay) {
    refs.fullscreenSpreadOverlay.textContent = spread.text_overlay_text;
    refs.fullscreenSpreadOverlay.style.left = `${values.x}%`;
    refs.fullscreenSpreadOverlay.style.top = `${values.y}%`;
    refs.fullscreenSpreadOverlay.style.width = `${values.width}%`;
    refs.fullscreenSpreadOverlay.style.textAlign = values.alignment;
    refs.fullscreenSpreadOverlay.style.backgroundColor = `rgba(255, 255, 255, ${values.wash_opacity})`;
    refs.fullscreenSpreadOverlay.style.opacity = isSpan && visible ? "1" : "0";
    refs.fullscreenSpreadOverlay.style.display = isSpan && visible ? "block" : "none";
  }
}

function attachOverlayDragTargets() {
  const targets = [
    { element: refs.previewOverlay, container: refs.spreadPreview },
    { element: refs.overlayTextLeft, container: refs.fullscreenLeft },
    { element: refs.overlayTextRight, container: refs.fullscreenRight },
    { element: refs.fullscreenSpreadOverlay, container: refs.fullscreenPages },
  ];
  targets.forEach(({ element, container }) => {
    if (!element || !container) return;
    element.addEventListener("pointerdown", (event) => startOverlayDrag(event, container));
  });
}

function startOverlayDrag(event, container) {
  if (!refs.overlayVisible?.checked) return;
  const spread = spreads.find((item) => item.spread_id === activeSpreadId);
  if (!spread) return;
  event.preventDefault();
  overlayDragState = {
    spread,
    container,
    overlay: { ...(spread.text_overlay || {}) },
  };
  document.addEventListener("pointermove", handleOverlayDragMove);
  document.addEventListener("pointerup", handleOverlayDragEnd);
  document.addEventListener("pointercancel", handleOverlayDragEnd);
}

function handleOverlayDragMove(event) {
  if (!overlayDragState) return;
  const rect = overlayDragState.container.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;
  const x = clamp(((event.clientX - rect.left) / rect.width) * 100, 0, 100);
  const y = clamp(((event.clientY - rect.top) / rect.height) * 100, 0, 100);
  overlayDragState.overlay = { ...overlayDragState.overlay, x, y };
  overlayDragState.spread.text_overlay = overlayDragState.overlay;
  refs.overlayX.value = Math.round(x);
  refs.overlayY.value = Math.round(y);
  updateOverlayVisual(overlayDragState.spread);
  updateFullscreenOverlay(overlayDragState.spread);
}

function handleOverlayDragEnd() {
  if (!overlayDragState) return;
  document.removeEventListener("pointermove", handleOverlayDragMove);
  document.removeEventListener("pointerup", handleOverlayDragEnd);
  document.removeEventListener("pointercancel", handleOverlayDragEnd);
  saveSpreadField("text_overlay", overlayDragState.overlay);
  overlayDragState = null;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function applySpreadOverridesToDrawer(spread) {
  const overrides = spread?.generation_overrides || {};
  const judgeModelValue = overrides.judge_model ?? generationConfig.judge_model ?? "";
  populateJudgeModelSelect(refs.drawerJudgeModel, { selected: judgeModelValue, includeBlank: false });
  const judgeThresholdValue = overrides.judge_threshold ?? generationConfig.judge_threshold;
  refs.drawerJudgeThreshold && (refs.drawerJudgeThreshold.value = thresholdToPreset(judgeThresholdValue));
  updateJudgePresetHelp(refs.drawerJudgeThreshold, refs.drawerJudgeThresholdHelp);
  const maxFailsValue = overrides.max_recursive_fails ?? generationConfig.max_recursive_fails;
  refs.drawerMaxFails &&
    (refs.drawerMaxFails.value =
      maxFailsValue === undefined || maxFailsValue === null ? "" : String(maxFailsValue));
  refs.drawerPromptStrategy &&
    (refs.drawerPromptStrategy.value =
      overrides.prompt_adjustment_strategy ?? generationConfig.prompt_adjustment_strategy ?? "suggestive");
  refs.drawerAllowUpdates &&
    (refs.drawerAllowUpdates.checked =
      overrides.allow_prompt_updates ?? generationConfig.allow_prompt_updates ?? false);
}

function applySpreadOverridesToGenerationForm(spread, useOverrides = true) {
  const overrides = useOverrides ? spread?.generation_overrides || {} : {};
  const judgeModelValue = overrides.judge_model ?? generationConfig.judge_model ?? "";
  populateJudgeModelSelect(refs.judgeModel, { selected: judgeModelValue, includeBlank: false });
  const judgeThresholdValue = overrides.judge_threshold ?? generationConfig.judge_threshold;
  refs.judgeThreshold && (refs.judgeThreshold.value = thresholdToPreset(judgeThresholdValue));
  updateJudgePresetHelp(refs.judgeThreshold, refs.judgeThresholdHelp);
  const maxFailsValue = overrides.max_recursive_fails ?? generationConfig.max_recursive_fails;
  refs.maxFails &&
    (refs.maxFails.value = maxFailsValue === undefined || maxFailsValue === null ? "" : String(maxFailsValue));
  refs.promptStrategy &&
    (refs.promptStrategy.value =
      overrides.prompt_adjustment_strategy ?? generationConfig.prompt_adjustment_strategy ?? "suggestive");
  refs.allowUpdates &&
    (refs.allowUpdates.checked =
      overrides.allow_prompt_updates ?? generationConfig.allow_prompt_updates ?? false);
}

function saveSpreadGenerationOverride(field, value) {
  if (!activeSpreadId || value === undefined) return;
  saveSpreadField("generation_overrides", { [field]: value }, true);
}

async function clearGenerationOverrides() {
  if (!activeSpreadId) return;
  await saveSpreadField("generation_overrides", null, true);
  selectSpread(activeSpreadId, { skipRender: true });
}

function snapOverlayToSafeMargin() {
  if (!activeSpreadId) return;
  const overlay = {
    visible: true,
    x: 7,
    y: 78,
    width: 86,
    alignment: "center",
    wash_opacity: 0.72,
  };
  refs.overlayVisible && (refs.overlayVisible.checked = overlay.visible);
  refs.overlayX && (refs.overlayX.value = overlay.x);
  refs.overlayY && (refs.overlayY.value = overlay.y);
  refs.overlayWidth && (refs.overlayWidth.value = overlay.width);
  refs.overlayAlignment && (refs.overlayAlignment.value = overlay.alignment);
  refs.overlayWash && (refs.overlayWash.value = overlay.wash_opacity);
  const spread = spreads.find((item) => item.spread_id === activeSpreadId);
  if (spread) {
    const updated = { ...spread, text_overlay: overlay };
    updateOverlayVisual(updated);
    updateFullscreenOverlay(updated);
  }
  saveSpreadField("text_overlay", overlay, true);
}

function parseNumberInput(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function updateTileHighlight() {
  document.querySelectorAll(".spread-tile").forEach((tile) => tile.classList.remove("active"));
  const selected = document.querySelector(`[data-id="${activeSpreadId}"]`);
  if (selected) {
    selected.classList.add("active");
    selected.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function openFullscreen() {
  refs.fullscreen.classList.add("visible");
  refs.fullscreen.setAttribute("aria-hidden", "false");
}

function closeFullscreen() {
  refs.fullscreen.classList.remove("visible");
  refs.fullscreen.setAttribute("aria-hidden", "true");
}

async function saveSpreadField(field, value, noRefresh = false) {
  if (!activeSpreadId) return;
  const updates = { [field]: value };
  const updated = await patchSpread(activeSpreadId, updates);
  spreads = spreads.map((item) => (item.spread_id === activeSpreadId ? updated : item));
  if (!noRefresh) renderGrid();
}

async function saveSpreadFieldsFromForm() {
  if (!activeSpreadId) return;
  await patchSpread(activeSpreadId, {
    prompt: refs.generatePrompt.value,
    negative_prompt: refs.generateNegative.value,
    seed: refs.generateSeed.value,
  });
}

function populateAssetSelect() {
  refs.assetControls.innerHTML = assets
    .map((asset) => `<option value="${asset.asset_id}">${asset.label} (${asset.source_type})</option>`)
    .join("\n");
}

function populateGenerateSelect() {
  refs.generateSpreadSelect.innerHTML = spreads
    .map((spread) => `<option value="${spread.spread_id}">${spread.spread_id.toUpperCase()} · ${spread.title}</option>`)
    .join("\n");
}

function formatTimestamp(value) {
  if (!value) return "";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleString();
}

async function patchSpread(spreadId, updates) {
  const response = await fetch(`/api/spreads/${spreadId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...updates, project_id: currentProjectId }),
  });
  if (!response.ok) {
    console.error("Failed to patch spread", await response.text());
    return null;
  }
  return response.json();
}

async function assignAsset(assetId) {
  if (!activeSpreadId) return;
  const updated = await patchSpread(activeSpreadId, { assigned_image_id: assetId });
  if (!updated) return;
  spreads = spreads.map((item) => (item.spread_id === activeSpreadId ? updated : item));
  await refreshAssets();
  renderGrid();
  selectSpread(activeSpreadId, { skipRender: true });
}

async function approveCandidate() {
  if (!activeSpreadId) return;
  refs.uploadStatus.textContent = "Promoting candidate into selects...";
  const response = await fetch(`/api/spreads/${activeSpreadId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: currentProjectId }),
  });
  if (!response.ok) {
    let message = `Approve failed (${response.status})`;
    try {
      const errorBody = await response.json();
      message = errorBody.error || message;
    } catch (_err) {
      // Ignore parse failures and fall back to status text.
    }
    refs.uploadStatus.textContent = message;
    return;
  }
  const updated = await response.json();
  spreads = spreads.map((item) => (item.spread_id === activeSpreadId ? updated : item));
  await refreshAssets();
  renderGrid();
  selectSpread(activeSpreadId, { skipRender: true });
  refs.uploadStatus.textContent = "Candidate promoted to approved select.";
}

async function clearAssignment() {
  if (!activeSpreadId) return;
  const updated = await patchSpread(activeSpreadId, { assigned_image_id: null });
  await refreshAssets();
  renderGrid();
  if (updated) {
    spreads = spreads.map((item) => (item.spread_id === activeSpreadId ? updated : item));
    selectSpread(activeSpreadId);
  }
}

function updateApproveButton(spread, asset) {
  if (!refs.approveCandidateBtn) return;
  const artState = getSpreadArtState(spread, asset, Boolean(getSpreadPreviewUrl(spread, asset)));
  const show = artState === "candidate";
  refs.approveCandidateBtn.hidden = !show;
  refs.approveCandidateBtn.disabled = !show;
}

async function handleFileUpload(file) {
  if (!activeSpreadId) return;
  refs.uploadStatus.textContent = `Uploading ${file.name}...`;
  const form = new FormData();
  form.append("file", file);
  form.append("spread_id", activeSpreadId);
  form.append("project_id", currentProjectId);
  form.append("label", file.name);
  const response = await fetch("/api/assets/upload", { method: "POST", body: form });
  if (!response.ok) {
    let message = `Upload failed (${response.status})`;
    try {
      const errorBody = await response.json();
      message = errorBody.error || message;
    } catch (_err) {
      // Ignore parse failures and fall back to status text.
    }
    refs.uploadStatus.textContent = message;
    return;
  }
  const asset = await response.json();
  await refreshAssets();
  if (asset.asset_id) {
    await assignAsset(asset.asset_id);
    refs.uploadStatus.textContent = `${file.name} assigned to ${activeSpreadId.toUpperCase()}.`;
  } else {
    refs.uploadStatus.textContent = `${file.name} uploaded.`;
  }
}

async function refreshAssets() {
  assets = await fetchJson(`/api/assets?project_id=${encodeURIComponent(currentProjectId)}`);
  populateAssetSelect();
  renderAssetsView();
}

function renderAssetsView() {
  refs.assetList.innerHTML = assets
    .map((asset) => {
      const assigned = (asset.spread_ids || []).join(", ") || "unused";
      const normalizedPath = (asset.run_path || "").replace(/\\\\/g, "/");
      const runFolder = normalizedPath ? normalizedPath.split("/").slice(-2, -1)[0] : "";
      const timestampLabel = formatTimestamp(asset.timestamp);
      const recursiveConfig = asset.recursive_config;
      const loopLabel = recursiveConfig
        ? `<span class="asset-meta">Judge loop: ${recursiveConfig.prompt_adjustment_strategy || "?"} / ${recursiveConfig.max_recursive_fails ?? "?"} fails</span>`
        : "";
      const attemptLabel = asset.attempt ? `<span class="asset-meta">Attempt: ${asset.attempt}</span>` : "";
      const failureLabel =
        typeof asset.failures === "number" && asset.failures > 0
          ? `<span class="asset-meta">Failures: ${asset.failures}</span>`
          : "";
      const metadataLink =
        asset.source_type === "run" && asset.asset_id
          ? `<span class="asset-meta asset-link-row">Metadata <a class="asset-link" href="/run-artifact/${encodeURIComponent(
              asset.asset_id
            )}/metadata.json" target="_blank" rel="noopener noreferrer">Open</a></span>`
          : "";
      return `
        <article class="asset-card">
          <div class="asset-preview" style="background-image: ${asset.mirror_url || "linear-gradient(135deg, #ede9fe, #fee2e2)"}"></div>
          <div class="asset-info">
            <strong>${asset.label}</strong>
            <span>${asset.source_type}</span>
            <span>Assigned: ${assigned}</span>
            ${asset.judge_score ? `<span>Score: ${Number(asset.judge_score).toFixed(2)}</span>` : ""}
            ${asset.judge_status ? `<span>Judge: ${asset.judge_status}</span>` : ""}
            ${timestampLabel ? `<span class="asset-meta">Saved: ${timestampLabel}</span>` : ""}
            ${runFolder ? `<span class="asset-meta asset-link-row">Run: ${runFolder} <a class="asset-link" href="/open-run/${encodeURIComponent(
        runFolder
      )}" target="_blank" rel="noopener noreferrer">Open folder</a></span>` : ""}
            ${loopLabel}
            ${attemptLabel}
            ${failureLabel}
            ${metadataLink}
          </div>
          <div class="asset-actions">
            <button data-action="assign" data-asset-id="${asset.asset_id}">Assign to spread</button>
            <button data-action="remove" data-asset-id="${asset.asset_id}">Remove from spread</button>
          </div>
        </article>
      `;
    })
    .join("\n");
}

refs.assetList?.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const assetId = button.dataset.assetId;
  if (!assetId) return;
  if (button.dataset.action === "assign") {
    await assignAsset(assetId);
    return;
  }
  if (button.dataset.action === "remove") {
    await clearAssignment();
  }
});

async function createPlaceholderAsset() {
  const gradient = `linear-gradient(135deg, hsl(${Math.floor(Math.random() * 360)}, 90%, 70%), hsl(${Math.floor(
    Math.random() * 360
  )}, 70%, 50%))`;
  const response = await fetch("/api/assets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label: "Placeholder", mirror_url: gradient, spread_ids: [], project_id: currentProjectId }),
  });
  const asset = await response.json();
  await refreshAssets();
  return asset;
}

function loadGenerationConfig() {
  populateJudgeModelSelect(refs.judgeModel, { selected: generationConfig.judge_model || "", includeBlank: false });
  refs.judgeThreshold.value = thresholdToPreset(generationConfig.judge_threshold || 0.78);
  updateJudgePresetHelp(refs.judgeThreshold, refs.judgeThresholdHelp);
  refs.maxFails.value = generationConfig.max_recursive_fails || 3;
  refs.promptStrategy.value = generationConfig.prompt_adjustment_strategy || "suggestive";
  refs.allowUpdates.checked = generationConfig.allow_prompt_updates || false;
}

function populateJudgePresetSelect(select) {
  if (!select) return;
  select.innerHTML = Object.entries(JUDGE_PRESETS)
    .map(([value, item]) => `<option value="${value}">${escapeHtml(item.label)}</option>`)
    .join("\n");
  select.addEventListener("change", () =>
    updateJudgePresetHelp(select, select === refs.drawerJudgeThreshold ? refs.drawerJudgeThresholdHelp : refs.judgeThresholdHelp)
  );
}

function presetToThreshold(value) {
  const preset = JUDGE_PRESETS[Number(value)];
  return preset ? preset.threshold : JUDGE_PRESETS[3].threshold;
}

function thresholdToPreset(value) {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return "3";
  let bestKey = "3";
  let bestDistance = Infinity;
  Object.entries(JUDGE_PRESETS).forEach(([key, preset]) => {
    const distance = Math.abs(preset.threshold - numeric);
    if (distance < bestDistance) {
      bestKey = key;
      bestDistance = distance;
    }
  });
  return bestKey;
}

function updateJudgePresetHelp(select, helpNode) {
  if (!select || !helpNode) return;
  const preset = JUDGE_PRESETS[Number(select.value)] || JUDGE_PRESETS[3];
  helpNode.textContent = `${select.value}. ${preset.label.split(". ")[1]}: ${preset.description}`;
}

function populateJudgeModelSelect(select, options = {}) {
  if (!select) return;
  const selected = options.selected ?? "";
  const includeBlank = options.includeBlank ?? false;
  const seen = new Set();
  const modelOptions = [];
  if (selected && !ollamaModels.some((item) => item.name === selected)) {
    modelOptions.push({
      value: selected,
      label: `${selected} (current default)`,
      title: "Configured model; not currently installed in Ollama list.",
    });
    seen.add(selected);
  }
  ollamaModels.forEach((item) => {
    if (!item?.name || seen.has(item.name)) return;
    const details = [item.size, item.modified].filter(Boolean).join(" • ");
    modelOptions.push({
      value: item.name,
      label: item.name,
      title: details,
    });
    seen.add(item.name);
  });
  select.innerHTML = "";
  if (includeBlank) {
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "Select a model";
    select.appendChild(blank);
  }
  modelOptions.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.value;
    option.textContent = item.label;
    if (item.title) {
      option.title = item.title;
    }
    select.appendChild(option);
  });
  if (selected) {
    select.value = selected;
  } else if (select.options.length) {
    select.selectedIndex = 0;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function shortPathLabel(value) {
  const normalized = String(value || "").replaceAll("\\", "/");
  const parts = normalized.split("/").filter(Boolean);
  return parts.slice(-3).join("/") || normalized;
}

async function runGenerator() {
  if (!activeSpreadId) return;
  const payload = {
    project_id: currentProjectId,
    spread_id: activeSpreadId,
    prompt: refs.generatePrompt.value,
    reference_notes: refs.referenceNotesField?.value || "",
    negative: refs.generateNegative.value,
    seed: refs.generateSeed.value,
    size: "1536x768",
    judge_model: refs.judgeModel.value || generationConfig.judge_model,
    judge_threshold: refs.judgeThreshold.value || generationConfig.judge_threshold,
    max_recursive_fails: refs.maxFails.value || generationConfig.max_recursive_fails,
    prompt_adjustment_strategy: refs.promptStrategy.value,
    allow_prompt_updates: refs.allowUpdates.checked ? "true" : "false",
  };
  const response = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  logGeneration(body.message || "Generation started");
  refs.generationStatus.textContent = body.message || "Generation requested";
  updateAbortButtonState({ running: true });
}

async function abortGenerator() {
  refs.generationStatus.textContent = "Killing active run...";
  const response = await fetch("/api/generate/abort", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const body = await response.json();
  refs.generationStatus.textContent = body.message || "Kill requested.";
  if (!body.aborted) {
    updateAbortButtonState(lastStatus || { running: false });
  }
}

function updateAbortButtonState(state) {
  if (!refs.abortGeneratorBtn) return;
  const running = Boolean(state?.running);
  refs.abortGeneratorBtn.disabled = !running;
}

function formatElapsedMs(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes <= 0) {
    return `${seconds}s`;
  }
  return `${minutes}m ${String(seconds).padStart(2, "0")}s`;
}

function buildGenerationStatusMeta(state) {
  if (!state?.running) {
    if (state?.last_error) {
      return "The last run stopped with an error.";
    }
    return "Waiting for a run.";
  }
  const startedAt = state?.attempt_started_at ? new Date(state.attempt_started_at) : null;
  const startedValid = startedAt && !Number.isNaN(startedAt.getTime());
  const elapsedMs = startedValid ? Date.now() - startedAt.getTime() : 0;
  const elapsedLabel = startedValid ? formatElapsedMs(elapsedMs) : "";
  const timeoutSeconds = Number(state?.attempt_timeout_seconds || 0);
  const timeoutMs = timeoutSeconds > 0 ? timeoutSeconds * 1000 : 0;
  const generatorLabel = String(state?.generator_label || "x/z-image-turbo");
  const lowerStatus = String(state?.status || "").toLowerCase();

  if (lowerStatus.includes("attempt") && lowerStatus.includes("generating")) {
    if (timeoutMs && elapsedMs > timeoutMs * 0.75) {
      return `Still rendering on GPU with ${generatorLabel}. ${elapsedLabel} elapsed, which is longer than usual.`;
    }
    return `Still rendering on GPU with ${generatorLabel}${elapsedLabel ? ` • ${elapsedLabel} elapsed` : ""}.`;
  }
  if (lowerStatus.includes("review")) {
    return "Image render finished. Running local review checks now.";
  }
  if (lowerStatus.includes("adjust")) {
    return "Rewriting the prompt from the latest review scorecard.";
  }
  return startedValid ? `${elapsedLabel} elapsed.` : "Workflow active.";
}

function startStatusPoll() {
  if (statusPollTimer) return;
  const poll = async () => {
    try {
      const state = await fetchJson("/api/status");
      refs.generationStatus.textContent = state.status || "Idle";
      if (refs.generationStatusMeta) {
        refs.generationStatusMeta.textContent = buildGenerationStatusMeta(state);
      }
      updateAbortButtonState(state);
      if (state.status && state.status !== lastStatus?.status) {
        logGeneration(state.status);
      }
      updateMagicBookModalState(state);
      if (lastStatus?.running && !state.running) {
        await refreshProjects();
        await refreshData();
        await refreshManuscriptData();
      }
      lastStatus = state;
    } catch (err) {
      console.error("Status poll failed", err);
    }
  };
  poll();
  statusPollTimer = setInterval(poll, 2500);
}

function logGeneration(message) {
  const entry = document.createElement("li");
  entry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
  refs.generateLog.prepend(entry);
  if (refs.generateLog.children.length > 12) {
    refs.generateLog.removeChild(refs.generateLog.lastChild);
  }
}

function loadGenerationForm(options = { useOverrides: true }) {
  const spread = spreads.find((item) => item.spread_id === activeSpreadId);
  if (!spread) return;
  refs.generatePrompt.value = spread.prompt || "";
  refs.generateNegative.value = spread.negative_prompt || "";
  refs.generateSeed.value = spread.seed || "";
  refs.generateSpreadSelect.value = spread.spread_id;
  applySpreadOverridesToGenerationForm(spread, options.useOverrides);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed ${response.status}`);
  }
  return response.json();
}

async function loadProject(projectId) {
  const response = await fetch("/api/projects/load", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId }),
  });
  if (!response.ok) {
    throw new Error(`Project load failed ${response.status}`);
  }
  return response.json();
}
