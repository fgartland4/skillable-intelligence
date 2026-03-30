/**
 * phase3.js — Phase 3 "Draft & Finalize" UI controller for Lab Program Designer v3.
 *
 * Layout: Center pane = interactive collapsible outline (Series → Labs → Activities).
 *         Right pane  = selected activity's instructions (top) + chat (bottom).
 *
 * Clicking an activity in the outline loads its draft instructions in the right pane
 * and scopes the chat context to that activity.
 *
 * Depends on: Store, Chat, Markdown (all global IIFEs).
 */

const Phase3 = (() => {

    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)];

    function escHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDuration(minutes) {
        if (!minutes) return '';
        if (typeof minutes === 'string') return minutes; // already formatted range
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        if (h === 0) return `${m}m`;
        if (m === 0) return `${h}h`;
        return `${h}h ${m}m`;
    }

    // ── State ───────────────────────────────────────────────────

    let _expandedLabs = new Set();   // which labs are expanded in the tree
    let _selectedActivityKey = null; // "labId::activityId"
    let _editingKey = null;          // key of activity currently being inline-edited

    function _parseKey(key) {
        if (!key) return { labId: null, activityId: null };
        const [labId, activityId] = key.split('::');
        return { labId, activityId };
    }
    function _makeKey(labId, activityId) {
        return `${labId}::${activityId}`;
    }

    // ── Init ────────────────────────────────────────────────────

    function init() {
        // Outline clicks (center pane)
        const outlineBody = $('#phase3-outline-body');
        if (outlineBody) {
            outlineBody.addEventListener('click', _handleOutlineClick);
        }

        // Style selector change (outline footer)
        const outlineFooter = $('#phase3-outline-footer');
        if (outlineFooter) {
            outlineFooter.addEventListener('change', (e) => {
                const select = e.target.closest('.p3-style-select');
                if (select) {
                    const projectId = select.dataset.projectId;
                    Store.setInstructionStyle(projectId, select.value);
                    const project = Store.getProject(projectId);
                    _renderOutlineFooter(project);
                }
            });
        }

        // Instructions viewer clicks (right pane)
        const viewer = $('#phase3-instructions-viewer');
        if (viewer) {
            viewer.addEventListener('click', _handleViewerClick);
        }
    }

    // ── Outline click handler ───────────────────────────────────

    function _handleOutlineClick(e) {
        const target = e.target;

        // Click a lab row → expand/collapse
        const labRow = target.closest('.p3-lab-row');
        if (labRow) {
            const labId = labRow.dataset.labId;
            if (_expandedLabs.has(labId)) {
                _expandedLabs.delete(labId);
            } else {
                _expandedLabs.add(labId);
            }
            const projectId = labRow.dataset.projectId;
            _renderOutline(Store.getProject(projectId));
            return;
        }

        // Click an activity row → select it
        const actRow = target.closest('.p3-activity-row');
        if (actRow) {
            const key = _makeKey(actRow.dataset.labId, actRow.dataset.activityId);
            _selectedActivityKey = key;
            _editingKey = null;
            const projectId = actRow.dataset.projectId;
            const project = Store.getProject(projectId);
            _renderOutline(project);
            _renderInstructions(project);
            return;
        }

        // "Draft All" button
        const draftAllBtn = target.closest('[data-draft-all]');
        if (draftAllBtn) {
            _handleDraftAll(draftAllBtn.dataset.projectId);
            return;
        }
    }

    // ── Instructions viewer click handler ───────────────────────

    function _handleViewerClick(e) {
        const target = e.target;

        // Toggle raw/preview
        const toggleBtn = target.closest('[data-toggle-view]');
        if (toggleBtn) {
            const viewer = $('#phase3-instructions-viewer');
            const preview = $('#p3-preview', viewer);
            const raw = $('#p3-raw', viewer);
            if (preview && raw) {
                const showingPreview = preview.style.display !== 'none';
                preview.style.display = showingPreview ? 'none' : 'block';
                raw.style.display = showingPreview ? 'block' : 'none';
                toggleBtn.textContent = showingPreview ? 'Preview' : 'Markdown';
            }
            return;
        }

        // Copy
        const copyBtn = target.closest('[data-copy-md]');
        if (copyBtn) {
            const { labId, activityId } = _parseKey(_selectedActivityKey);
            const project = Store.getProject(copyBtn.dataset.projectId);
            if (project && project.draftInstructions && project.draftInstructions[labId]) {
                const md = project.draftInstructions[labId][activityId];
                if (md) {
                    navigator.clipboard.writeText(md).then(() => {
                        copyBtn.textContent = 'Copied!';
                        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
                    });
                }
            }
            return;
        }

        // Edit
        const editBtn = target.closest('[data-edit-md]');
        if (editBtn) {
            _editingKey = _selectedActivityKey;
            _renderInstructions(Store.getProject(editBtn.dataset.projectId));
            return;
        }

        // Save edit
        const saveBtn = target.closest('[data-save-edit]');
        if (saveBtn) {
            const textarea = $('#p3-edit-textarea');
            if (textarea) {
                const { labId, activityId } = _parseKey(_selectedActivityKey);
                _saveDraftInstructions(saveBtn.dataset.projectId, labId, activityId, textarea.value);
                _editingKey = null;
                const project = Store.getProject(saveBtn.dataset.projectId);
                _renderOutline(project);
                _renderInstructions(project);
            }
            return;
        }

        // Cancel edit
        const cancelBtn = target.closest('[data-cancel-edit]');
        if (cancelBtn) {
            _editingKey = null;
            _renderInstructions(Store.getProject(cancelBtn.dataset.projectId));
            return;
        }

        // Regenerate
        const regenBtn = target.closest('[data-regen]');
        if (regenBtn) {
            const { labId, activityId } = _parseKey(_selectedActivityKey);
            handleGenerateActivityInstructions(labId, activityId, regenBtn.dataset.projectId);
            return;
        }

        // Generate (for activity with no draft yet)
        const generateBtn = target.closest('[data-generate]');
        if (generateBtn) {
            const { labId, activityId } = _parseKey(_selectedActivityKey);
            handleGenerateActivityInstructions(labId, activityId, generateBtn.dataset.projectId);
            return;
        }
    }

    // ── Main render entry point ─────────────────────────────────

    function render(project) {
        if (!project) return;
        _renderOutline(project);
        _renderInstructions(project);
        _renderOutlineFooter(project);
    }

    // ── Outline (center pane) ───────────────────────────────────

    function _renderOutline(project) {
        const container = $('#phase3-outline-body');
        if (!container) return;

        const structure = project.programStructure;
        if (!structure || !structure.labSeries || structure.labSeries.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No program structure yet.</p>
                    <p class="hint">Complete Phase 2 to define your Lab Series, Labs, and Activities.</p>
                </div>
            `;
            return;
        }

        let html = '';
        for (const ls of structure.labSeries) {
            html += `<div class="p3-series-block">`;
            html += `<div class="p3-series-header">${escHtml(ls.title)}</div>`;

            for (const lab of (ls.labs || [])) {
                const isExpanded = _expandedLabs.has(lab.id);
                const activities = lab.activities || [];
                const draftedCount = activities.filter(a => _hasInstructions(lab.id, a.id, project)).length;
                const totalCount = activities.length;
                const allDrafted = draftedCount === totalCount && totalCount > 0;

                html += `
                    <div class="p3-lab-row${isExpanded ? ' expanded' : ''}" data-lab-id="${lab.id}" data-project-id="${project.id}">
                        <span class="p3-lab-chevron">${isExpanded ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>' : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>'}</span>
                        <span class="p3-lab-title">${escHtml(lab.title)}</span>
                        <span class="p3-lab-badge ${allDrafted ? 'complete' : ''}">${draftedCount}/${totalCount}</span>
                    </div>
                `;

                if (isExpanded) {
                    html += `<div class="p3-activity-list">`;
                    for (const act of activities) {
                        const key = _makeKey(lab.id, act.id);
                        const isSelected = _selectedActivityKey === key;
                        const hasDraft = _hasInstructions(lab.id, act.id, project);
                        const statusClass = hasDraft ? 'drafted' : 'empty';

                        html += `
                            <div class="p3-activity-row ${statusClass}${isSelected ? ' selected' : ''}"
                                 data-lab-id="${lab.id}" data-activity-id="${act.id}" data-project-id="${project.id}">
                                <span class="p3-activity-status" title="${hasDraft ? 'Draft ready' : 'No draft yet'}"></span>
                                <span class="p3-activity-title">${escHtml(act.title)}</span>
                            </div>
                        `;
                    }
                    html += `</div>`;
                }
            }
            html += `</div>`;
        }

        container.innerHTML = html;
    }

    // ── Outline footer (styling + draft all) ────────────────────

    function _renderOutlineFooter(project) {
        const footer = $('#phase3-outline-footer');
        if (!footer) return;

        const structure = project.programStructure;
        const hasStructure = structure && structure.labSeries && structure.labSeries.length > 0;
        if (!hasStructure) {
            footer.innerHTML = '';
            return;
        }

        // Count total activities and drafted
        let total = 0, drafted = 0;
        for (const ls of structure.labSeries) {
            for (const lab of (ls.labs || [])) {
                for (const act of (lab.activities || [])) {
                    total++;
                    if (_hasInstructions(lab.id, act.id, project)) drafted++;
                }
            }
        }

        const instructionStyle = project.instructionStyle || 'challenge';
        const styleLabels = {
            'challenge': 'Challenge-based',
            'mixed': 'Mixed',
            'performance-test': 'Performance Test',
            'step-by-step': 'Step-by-step',
        };

        footer.innerHTML = `
            <div class="p3-footer-stats">
                <span class="p3-stat">${drafted}/${total} activities drafted</span>
                <span class="p3-stat-sep">&middot;</span>
                <span class="p3-stat p3-style-label">Style:</span>
                <select class="p3-style-select" data-project-id="${project.id}" title="Instruction style">
                    <option value="challenge"${instructionStyle === 'challenge' ? ' selected' : ''}>Challenge-based</option>
                    <option value="step-by-step"${instructionStyle === 'step-by-step' ? ' selected' : ''}>Step-by-step</option>
                    <option value="mixed"${instructionStyle === 'mixed' ? ' selected' : ''}>Mixed</option>
                    <option value="performance-test"${instructionStyle === 'performance-test' ? ' selected' : ''}>Performance Test</option>
                </select>
            </div>
            ${drafted < total ? `<button class="btn btn-primary btn-sm" data-draft-all data-project-id="${project.id}">Draft All Remaining</button>` : ''}
        `;
    }

    // ── Instructions viewer (right pane top) ────────────────────

    function _renderInstructions(project) {
        const viewer = $('#phase3-instructions-viewer');
        if (!viewer) return;

        if (!_selectedActivityKey) {
            viewer.innerHTML = `
                <div class="empty-state">
                    <p>Select an activity from the outline.</p>
                    <p class="hint">Click any activity to view or generate its draft instructions.</p>
                </div>
            `;
            return;
        }

        const { labId, activityId } = _parseKey(_selectedActivityKey);
        const structure = project.programStructure;

        // Find the activity
        let labTitle = '', actTitle = '', actDescription = '';
        if (structure && structure.labSeries) {
            for (const ls of structure.labSeries) {
                for (const lab of (ls.labs || [])) {
                    if (lab.id === labId) {
                        labTitle = lab.title;
                        for (const act of (lab.activities || [])) {
                            if (act.id === activityId) {
                                actTitle = act.title;
                                actDescription = act.description || '';
                                break;
                            }
                        }
                        break;
                    }
                }
            }
        }

        const hasDraft = _hasInstructions(labId, activityId, project);
        const isEditing = _editingKey === _selectedActivityKey;

        let html = `
            <div class="p3-viewer-header">
                <div class="p3-viewer-breadcrumb">${escHtml(labTitle)}</div>
                <div class="p3-viewer-title">${escHtml(actTitle)}</div>
                ${actDescription ? `<div class="p3-viewer-desc">${escHtml(actDescription)}</div>` : ''}
            </div>
        `;

        if (isEditing && hasDraft) {
            const md = project.draftInstructions[labId][activityId];
            html += `
                <div class="p3-viewer-content">
                    <textarea id="p3-edit-textarea" class="p3-edit-textarea">${escHtml(md)}</textarea>
                    <div class="p3-edit-actions">
                        <button class="btn btn-primary btn-sm" data-save-edit data-project-id="${project.id}">Save</button>
                        <button class="btn btn-ghost btn-sm" data-cancel-edit data-project-id="${project.id}">Cancel</button>
                    </div>
                </div>
            `;
        } else if (hasDraft) {
            const md = project.draftInstructions[labId][activityId];
            const renderedHtml = typeof Markdown !== 'undefined' ? Markdown.render(md) : `<pre>${escHtml(md)}</pre>`;
            html += `
                <div class="p3-viewer-actions">
                    <button class="btn btn-ghost btn-sm" data-toggle-view>Markdown</button>
                    <button class="btn btn-ghost btn-sm" data-copy-md data-project-id="${project.id}">Copy</button>
                    <button class="btn btn-ghost btn-sm" data-edit-md data-project-id="${project.id}">Edit</button>
                    <button class="btn btn-ghost btn-sm" data-regen data-project-id="${project.id}">Regenerate</button>
                </div>
                <div class="p3-viewer-content">
                    <div id="p3-preview" class="p3-instructions-rendered">${renderedHtml}</div>
                    <div id="p3-raw" class="p3-instructions-raw" style="display:none;"><pre>${escHtml(md)}</pre></div>
                </div>
            `;
        } else {
            html += `
                <div class="p3-viewer-content p3-no-draft">
                    <p>No draft instructions yet for this activity.</p>
                    <button class="btn btn-primary btn-sm" data-generate data-project-id="${project.id}">Generate Draft</button>
                    <p class="hint">Or describe what you want in the chat below and I'll draft it for you.</p>
                </div>
            `;
        }

        viewer.innerHTML = html;
    }

    // ── Helpers ──────────────────────────────────────────────────

    function _hasInstructions(labId, activityId, project) {
        return project.draftInstructions &&
            project.draftInstructions[labId] &&
            project.draftInstructions[labId][activityId];
    }

    function _saveDraftInstructions(projectId, labId, activityId, markdown) {
        const project = Store.getProject(projectId);
        if (!project) return;
        if (!project.draftInstructions) project.draftInstructions = {};
        if (!project.draftInstructions[labId]) project.draftInstructions[labId] = {};
        project.draftInstructions[labId][activityId] = markdown;
        Store.updateProject(project);
    }

    // ── Generate instructions ───────────────────────────────────

    async function handleGenerateActivityInstructions(labId, activityId, projectId) {
        const project = Store.getProject(projectId);
        if (!project || !project.programStructure) return;

        // Find the activity
        let labTitle = '', actTitle = '', actDescription = '';
        for (const ls of (project.programStructure.labSeries || [])) {
            for (const lab of (ls.labs || [])) {
                if (lab.id === labId) {
                    labTitle = lab.title;
                    for (const act of (lab.activities || [])) {
                        if (act.id === activityId) {
                            actTitle = act.title;
                            actDescription = act.description || '';
                            break;
                        }
                    }
                    break;
                }
            }
        }

        // Show generating state
        const viewer = $('#phase3-instructions-viewer');
        if (viewer) {
            viewer.innerHTML = `
                <div class="p3-viewer-header">
                    <div class="p3-viewer-breadcrumb">${escHtml(labTitle)}</div>
                    <div class="p3-viewer-title">${escHtml(actTitle)}</div>
                </div>
                <div class="p3-viewer-content p3-generating">
                    <div class="typing-indicator"><span></span><span></span><span></span></div>
                    <p>Generating draft instructions...</p>
                </div>
            `;
        }

        const prompt = `Generate detailed draft instructions for this activity:\n\n` +
            `Lab: ${labTitle}\nActivity: ${actTitle}\n` +
            (actDescription ? `Description: ${actDescription}\n` : '') +
            `\nPlease provide complete step-by-step instructions in markdown format. ` +
            `Wrap the instructions in ===DRAFT_INSTRUCTIONS=== markers with labId "${labId}" and activityId "${activityId}".`;

        try {
            const result = await Chat.sendMessage(3, projectId, prompt);
            if (result.structured && result.structured.draftInstructions) {
                const draft = result.structured.draftInstructions;
                _saveDraftInstructions(projectId, draft.labId || labId, draft.activityId || activityId, draft.markdown || '');
            }
            const updatedProject = Store.getProject(projectId);
            _renderOutline(updatedProject);
            _renderInstructions(updatedProject);
            _renderOutlineFooter(updatedProject);
        } catch (err) {
            console.error('[Phase3] Failed to generate instructions:', err);
            if (viewer) {
                viewer.innerHTML = `
                    <div class="p3-viewer-content p3-no-draft">
                        <p>Failed to generate: ${escHtml(err.message)}</p>
                        <button class="btn btn-primary btn-sm" data-generate data-project-id="${projectId}">Try Again</button>
                    </div>
                `;
            }
        }
    }

    async function _handleDraftAll(projectId) {
        const project = Store.getProject(projectId);
        if (!project || !project.programStructure) return;

        for (const ls of (project.programStructure.labSeries || [])) {
            for (const lab of (ls.labs || [])) {
                for (const act of (lab.activities || [])) {
                    if (!_hasInstructions(lab.id, act.id, project)) {
                        _selectedActivityKey = _makeKey(lab.id, act.id);
                        _expandedLabs.add(lab.id);
                        await handleGenerateActivityInstructions(lab.id, act.id, projectId);
                    }
                }
            }
        }
    }

    // ── AI results integration ──────────────────────────────────

    function applyAIResults(structured, projectId) {
        if (!structured) return;

        // Handle LAB_BLUEPRINTS
        if (structured.blueprints && Array.isArray(structured.blueprints)) {
            const project = Store.getProject(projectId);
            if (project) {
                const existing = project.labBlueprints || [];
                for (const bp of structured.blueprints) {
                    const normalized = {
                        id: bp.id || Store.generateId(),
                        title: bp.title || '',
                        shortDescription: bp.shortDescription || bp.description || '',
                        estimatedDuration: bp.estimatedDuration || 0,
                        activities: (bp.activities || []).map(a => ({
                            title: a.title || '',
                            tasks: a.tasks || [],
                            duration: a.duration || 0,
                        })),
                        approved: { title: null, description: null, outline: null },
                    };
                    const existingIdx = existing.findIndex(e => e.id === bp.id);
                    if (existingIdx >= 0) {
                        existing[existingIdx] = normalized;
                    } else {
                        existing.push(normalized);
                    }
                }
                project.labBlueprints = existing;
                Store.updateProject(project);
            }
        }

        // Handle DRAFT_INSTRUCTIONS
        if (structured.draftInstructions) {
            const draft = structured.draftInstructions;
            if (draft.labId && draft.activityId && draft.markdown) {
                _saveDraftInstructions(projectId, draft.labId, draft.activityId, draft.markdown);
                // Auto-select the activity that just got instructions
                _selectedActivityKey = _makeKey(draft.labId, draft.activityId);
                _expandedLabs.add(draft.labId);
            } else if (draft.labId && draft.markdown) {
                Store.setDraftInstructions(projectId, draft.labId, draft.markdown);
            }
        }

        render(Store.getProject(projectId));
    }

    // ── Context Summary ─────────────────────────────────────────

    function getContextSummary(projectId) {
        const project = Store.getProject(projectId);
        if (!project) return '';

        const lines = ['Phase 3 — Draft & Finalize'];

        // Selected activity context
        if (_selectedActivityKey) {
            const { labId, activityId } = _parseKey(_selectedActivityKey);
            lines.push(`Currently editing: ${labId} / ${activityId}`);
        }

        const instructions = project.draftInstructions || {};
        const labCount = Object.keys(instructions).length;
        let activityCount = 0;
        for (const labInstructions of Object.values(instructions)) {
            if (typeof labInstructions === 'object') {
                activityCount += Object.keys(labInstructions).length;
            }
        }

        lines.push(`Draft instructions: ${activityCount} activities across ${labCount} labs`);
        return lines.join('\n');
    }

    // ── Public API ──────────────────────────────────────────────

    return {
        init,
        render,
        applyAIResults,
        getContextSummary,
    };
})();
