const statusLabels = {
  draft: "Draft",
  "needs-work": "Needs work",
  approved: "Approved",
  missing: "Missing asset",
};

const fallbackPalette = {
  span: "linear-gradient(135deg, #e0f2fe, #fef3c7)",
  left: "linear-gradient(135deg, #ede9fe, #fee2e2)",
  right: "linear-gradient(135deg, #fef2f2, #f9fafb)",
  inset: "linear-gradient(135deg, #ecfccb, #dbeafe)",
  "text-only": "linear-gradient(135deg, #f5f3ff, #ede9fe)",
};

let spreads = [];
let assets = [];
let generationConfig = {};
let activeSpreadId = null;
let statusPollTimer = null;
let lastStatus = null;
let overlayDragState = null;

const refs = {};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  cacheElements();
  attachListeners();
  await refreshData();
  startStatusPoll();
}

function cacheElements() {
  const ids = [
    "spreadGrid",
    "drawerTitle",
    "spreadPreview",
    "previewOverlay",
    "dropTarget",
    "promptField",
    "negativeField",
    "seedField",
    "notesField",
    "statusSelect",
    "promptStatus",
    "uploadStatus",
    "lastUpdated",
    "assetSelect",
    "generationStatus",
    "generationLog",
    "generateSpreadSelect",
    "generatePrompt",
    "generateNegative",
    "generateSeed",
    "judgeModel",
    "judgeThreshold",
    "maxFails",
    "promptStrategy",
    "allowUpdates",
    "drawerJudgeModel",
    "drawerJudgeThreshold",
    "drawerMaxFails",
    "drawerPromptStrategy",
    "drawerAllowUpdates",
    "snapOverlayBtn",
    "clearJudgeOverridesBtn",
    "fullscreenToggleOverlay",
  ];
  ids.forEach((id) => {
    refs[id] = document.getElementById(id);
  });
  refs.layoutGrid = document.getElementById("spreadGrid");
  refs.tabButtons = document.querySelectorAll(".tabs .tab");
  refs.layoutView = document.getElementById("layoutView");
  refs.generateView = document.getElementById("generateView");
  refs.assetsView = document.getElementById("assetsView");
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
  refs.fullscreen = document.getElementById("fullscreenOverlay");
  refs.fullscreenLeft = document.getElementById("fullscreenLeft");
  refs.fullscreenRight = document.getElementById("fullscreenRight");
  refs.generateLog = document.getElementById("generationLog");
  refs.generateStatus = document.getElementById("generationStatus");
}

function attachListeners() {
  refs.layoutGrid.addEventListener("click", (event) => {
    const openButton = event.target.closest("[data-action='open-spread']");
    const tile = event.target.closest(".spread-tile");
    if (!tile) return;
    selectSpread(tile.dataset.id, { focusDrawer: true });
    if (openButton) {
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
      const overlay = {
        visible: refs.overlayVisible.checked,
        x: Number(refs.overlayX.value),
        y: Number(refs.overlayY.value),
        width: Number(refs.overlayWidth.value),
        alignment: refs.overlayAlignment.value,
        wash_opacity: Number(refs.overlayWash.value),
      };
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

  document.getElementById("chooseAssetBtn").addEventListener("click", () => showTab("assets"));
  document.getElementById("uploadBtn").addEventListener("click", () => document.getElementById("hiddenUpload").click());
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
    if (!refs.overlayVisible) return;
    refs.overlayVisible.checked = !refs.overlayVisible.checked;
    refs.overlayVisible.dispatchEvent(new Event("input", { bubbles: true }));
  });

  refs.tabButtons.forEach((button) => {
    button.addEventListener("click", () => showTab(button.dataset.tab));
  });

  refs.drawerJudgeModel?.addEventListener("input", () => saveSpreadGenerationOverride("judge_model", refs.drawerJudgeModel.value));
  refs.drawerJudgeThreshold?.addEventListener("input", () =>
    saveSpreadGenerationOverride("judge_threshold", parseNumberInput(refs.drawerJudgeThreshold.value))
  );
  refs.drawerMaxFails?.addEventListener("input", () =>
    saveSpreadGenerationOverride("max_recursive_fails", parseNumberInput(refs.drawerMaxFails.value))
  );
  refs.drawerPromptStrategy?.addEventListener("change", () => saveSpreadGenerationOverride("prompt_adjustment_strategy", refs.drawerPromptStrategy.value));
  refs.drawerAllowUpdates?.addEventListener("change", () => saveSpreadGenerationOverride("allow_prompt_updates", refs.drawerAllowUpdates.checked));
  refs.clearJudgeOverridesBtn?.addEventListener("click", () => clearGenerationOverrides());

  refs.judgeModel?.addEventListener("input", () => saveSpreadGenerationOverride("judge_model", refs.judgeModel.value));
  refs.judgeThreshold?.addEventListener("input", () =>
    saveSpreadGenerationOverride("judge_threshold", parseNumberInput(refs.judgeThreshold.value))
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
  document.getElementById("generateReset").addEventListener("click", () => {
    loadGenerationConfig();
    loadGenerationForm({ useOverrides: false });
  });
  document.getElementById("clearAssignmentBtn").addEventListener("click", () => clearAssignment());
  document.getElementById("zoomReset").addEventListener("click", () => refs.layoutGrid.scrollTo({ top: 0, behavior: "smooth" }));
  document.getElementById("addAssetBtn").addEventListener("click", createPlaceholderAsset);
  document.addEventListener("keydown", (event) => {
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
}

function showTab(name) {
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
}

async function refreshData() {
  spreads = await fetchJson("/api/spreads");
  const assetResponse = await fetchJson("/api/assets");
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
}

function renderGrid() {
  refs.layoutGrid.innerHTML = spreads
    .map((spread) => {
      const asset = assets.find((item) => item.asset_id === spread.assigned_image_id);
      const hasImage = Boolean(asset?.mirror_url);
      const previewStyle = hasImage
        ? `url(${asset.mirror_url})`
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
            <span class="status-${spread.status.replace(" ", "-")}">${statusLabels[spread.status] || spread.status}</span>
            <span class="layout-type">${spread.layout_type}</span>
            ${hasImage ? "" : "<span class=\"tile-warning-dot\" title=\"Spread missing art\"></span>"}
          </div>
          <div class="tile-cta-row">
            <span class="tile-cta-hint">Double-click to open spread</span>
            <button class="ghost-btn tile-open-btn" type="button" data-action="open-spread">Open spread</button>
          </div>
        </article>
      `;
    })
    .join("\n");
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
  refs.promptField.value = spread.prompt;
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
  updateOverlayVisual(spread);
  updateFullscreenOverlay(spread);
  applySpreadOverridesToDrawer(spread);
  if (refs.generateSpreadSelect) {
    refs.generateSpreadSelect.value = spread.spread_id;
  }
  loadGenerationForm();
}

function applyPreview(spread, asset) {
  const fallback = fallbackPalette[spread.layout_type] || fallbackPalette.span;
  const background = asset?.mirror_url ? `url(${asset.mirror_url})` : fallback;
  refs.spreadPreview.style.backgroundImage = background;
  refs.fullscreenLeft.style.backgroundImage = background;
  refs.fullscreenRight.style.backgroundImage = background;
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
  refs.previewOverlay.style.opacity = values.visible ? "1" : "0";
  refs.previewOverlay.style.display = values.visible ? "block" : "none";
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
  [refs.overlayTextLeft, refs.overlayTextRight].forEach((el) => {
    el.style.left = `${values.x}%`;
    el.style.top = `${values.y}%`;
    el.style.width = `${values.width}%`;
    el.style.textAlign = values.alignment;
    el.style.backgroundColor = `rgba(255, 255, 255, ${values.wash_opacity})`;
    el.style.opacity = visible ? "1" : "0";
    el.style.display = visible ? "block" : "none";
  });
}

function attachOverlayDragTargets() {
  const targets = [
    { element: refs.previewOverlay, container: refs.spreadPreview },
    { element: refs.overlayTextLeft, container: refs.fullscreenLeft },
    { element: refs.overlayTextRight, container: refs.fullscreenRight },
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
  refs.drawerJudgeModel && (refs.drawerJudgeModel.value = judgeModelValue);
  const judgeThresholdValue = overrides.judge_threshold ?? generationConfig.judge_threshold;
  refs.drawerJudgeThreshold &&
    (refs.drawerJudgeThreshold.value =
      judgeThresholdValue === undefined || judgeThresholdValue === null ? "" : String(judgeThresholdValue));
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
  refs.judgeModel && (refs.judgeModel.value = judgeModelValue);
  const judgeThresholdValue = overrides.judge_threshold ?? generationConfig.judge_threshold;
  refs.judgeThreshold &&
    (refs.judgeThreshold.value =
      judgeThresholdValue === undefined || judgeThresholdValue === null ? "" : String(judgeThresholdValue));
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
    x: 8,
    y: 22,
    width: 60,
    alignment: "left",
    wash_opacity: 0.65,
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
    body: JSON.stringify(updates),
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

async function handleFileUpload(file) {
  if (!activeSpreadId) return;
  refs.uploadStatus.textContent = `Uploading ${file.name}...`;
  const form = new FormData();
  form.append("file", file);
  form.append("spread_id", activeSpreadId);
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
  assets = await fetchJson("/api/assets");
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
    body: JSON.stringify({ label: "Placeholder", mirror_url: gradient, spread_ids: [] }),
  });
  const asset = await response.json();
  await refreshAssets();
  return asset;
}

function loadGenerationConfig() {
  refs.judgeModel.value = generationConfig.judge_model || "";
  refs.judgeThreshold.value = generationConfig.judge_threshold || 0.75;
  refs.maxFails.value = generationConfig.max_recursive_fails || 3;
  refs.promptStrategy.value = generationConfig.prompt_adjustment_strategy || "suggestive";
  refs.allowUpdates.checked = generationConfig.allow_prompt_updates || false;
}

async function runGenerator() {
  if (!activeSpreadId) return;
  const payload = {
    spread_id: activeSpreadId,
    prompt: refs.generatePrompt.value,
    negative: refs.generateNegative.value,
    seed: refs.generateSeed.value,
    size: "1024x1024",
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
}

function startStatusPoll() {
  if (statusPollTimer) return;
  statusPollTimer = setInterval(async () => {
    try {
      const state = await fetchJson("/api/status");
      refs.generationStatus.textContent = state.status || "Idle";
      if (lastStatus?.running && !state.running) {
        await refreshData();
      }
      lastStatus = state;
    } catch (err) {
      console.error("Status poll failed", err);
    }
  }, 2500);
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
