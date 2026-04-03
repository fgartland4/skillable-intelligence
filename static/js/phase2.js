/**
 * phase2.js — Phase 2 "Design & Organize" UI controller for Lab Program Designer v3.
 * Manages the split-panel layout: chat on the left, context panel on the right.
 * Context panel shows a collapsible outline: Lab Series → Labs → Activities.
 * Tabs: Lab Outline (with add/delete/reorder), Skill Mapping (AI-auto with approve/override).
 */

const Phase2 = (() => {

    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)];

    function _genId() {
        return typeof Store !== 'undefined' && Store.generateId ? Store.generateId() : 'n' + Date.now() + Math.random().toString(36).slice(2, 6);
    }

    // ── Initialisation ───────────────────────────────────────────

    let _outlineEventsBound = false;
    let _skillMappingEventsBound = false;
    let _currentMappingProject = null;
    let _currentMappingTargets = [];

    /**
     * Bind skill mapping events once on the persistent #phase2-framework-content.
     * Uses _currentMappingProject/_currentMappingTargets for fresh data on each click.
     */
    function _bindSkillMappingEventsOnce(content) {
        if (_skillMappingEventsBound) return;
        _skillMappingEventsBound = true;

        content.addEventListener('change', (e) => {
            // Framework select
            if (e.target.id === 'phase2-framework-select') {
                handleFrameworkSelect(e.target.value, _currentMappingProject?.id);
                return;
            }
            // Mapping target select
            const targetSelect = e.target.closest('.mapping-target-select');
            if (targetSelect && _currentMappingProject) {
                const idx = parseInt(targetSelect.dataset.mappingIdx);
                const selectedOpt = targetSelect.selectedOptions[0];
                const targetId = targetSelect.value;
                const targetType = selectedOpt ? selectedOpt.dataset.type : 'lab';
                _updateMappingTarget(_currentMappingProject.id, idx, targetId, targetType);
            }
        });

        content.addEventListener('click', (e) => {
            // Auto-map button
            if (e.target.closest('#phase2-auto-map') && _currentMappingProject) {
                _autoMapSkills(_currentMappingProject, _currentMappingTargets);
                return;
            }
            // Approve all button
            if (e.target.closest('#phase2-approve-all') && _currentMappingProject) {
                _approveAll(_currentMappingProject.id);
                return;
            }
            // Re-map button
            if (e.target.closest('#phase2-remap') && _currentMappingProject) {
                const p = Store.getProject(_currentMappingProject.id);
                if (p) { p.skillMappings = []; Store.updateProject(p); renderSkillMapping(p); }
                return;
            }
            // Approve/unapprove individual mapping
            const approveBtn = e.target.closest('.mapping-approve-btn');
            if (approveBtn && _currentMappingProject) {
                _setMappingApproved(_currentMappingProject.id, parseInt(approveBtn.dataset.mappingIdx), true);
                return;
            }
            const unapproveBtn = e.target.closest('.mapping-unapprove-btn');
            if (unapproveBtn && _currentMappingProject) {
                _setMappingApproved(_currentMappingProject.id, parseInt(unapproveBtn.dataset.mappingIdx), false);
                return;
            }
        });
    }

    function init() {
        const container = _getContainer();
        if (!container) return;

        _bindTabButtons(container);
        _bindFrameworkUploadInput(container);
    }

    /**
     * Bind outline tree events once on the persistent #phase2-outline-tree element.
     * Called from renderOutline() but guarded so listeners are only added once —
     * the tree container persists across innerHTML replacements.
     */
    function _bindOutlineEventsOnce() {
        if (_outlineEventsBound) return;
        const container = $('#phase2-outline-tree');
        if (!container) return;
        _bindOutlineEvents(container);
        _outlineEventsBound = true;
    }

    function _getContainer() {
        // Render into center-pane-body if it exists, otherwise fall back to #phase2-context
        return $('#phase2-context .center-pane-body') || $('#phase2-context');
    }

    function _bindTabButtons(container) {
        container.addEventListener('click', (e) => {
            const tabBtn = e.target.closest('[data-phase2-tab]');
            if (!tabBtn) return;

            const tabName = tabBtn.dataset.phase2Tab;
            $$('[data-phase2-tab]', container).forEach(b => b.classList.remove('active'));
            tabBtn.classList.add('active');
            $$('.phase2-tab-panel', container).forEach(p => p.classList.remove('active'));
            const panel = $(`#phase2-tab-${tabName}`, container);
            if (panel) panel.classList.add('active');
        });
    }

    function _bindFrameworkUploadInput(container) {
        container.addEventListener('change', (e) => {
            if (e.target.id === 'phase2-framework-upload') {
                const file = e.target.files[0];
                if (file) handleFrameworkUpload(file);
                e.target.value = '';
            }
        });
    }

    // ── Full render ──────────────────────────────────────────────

    function render(project) {
        const container = _getContainer();
        if (!container) return;

        container.innerHTML = _buildTabsShell(project);
        renderOutline(project.programStructure);
        renderSkillMapping(project);

        const firstBtn = $('[data-phase2-tab]', container);
        if (firstBtn) firstBtn.click();

        // Tab and framework upload listeners are bound once in init() on the
        // persistent container — do NOT re-bind here.  The container survives
        // innerHTML replacement (only children are destroyed), so the init()
        // listeners remain active via event delegation.
    }

    function _buildTabsShell(project) {
        const programName = (project && project.name && project.name !== 'Untitled Program') ? project.name : '';
        return `
            <div class="bp-header">
                <h3 class="bp-title">Lab Blueprint</h3>
                ${programName ? `<div class="bp-program-name">${_escHtml(programName)}</div>` : ''}
            </div>

            <div class="phase2-tabs">
                <button class="context-tab active" data-phase2-tab="outline">Lab Outline</button>
                <button class="context-tab" data-phase2-tab="framework">Skill Mapping</button>
            </div>

            <div id="phase2-tab-outline" class="phase2-tab-panel active">
                <div class="phase2-outline-toolbar">
                    <button id="phase2-expand-all" class="btn-sm" title="Expand All">Expand All</button>
                    <button id="phase2-collapse-all" class="btn-sm" title="Collapse All">Collapse All</button>
                    <button id="phase2-add-series" class="btn-sm btn-add" title="Add Lab Series">+ Series</button>
                </div>
                <div id="phase2-outline-tree"></div>
            </div>

            <div id="phase2-tab-framework" class="phase2-tab-panel">
                <div id="phase2-framework-content"></div>
            </div>
        `;
    }

    // ══════════════════════════════════════════════════════════════
    //  Tab 1: Lab Outline (with add / delete / reorder)
    // ══════════════════════════════════════════════════════════════

    function renderOutline(programStructure) {
        const treeContainer = $('#phase2-outline-tree');
        if (!treeContainer) return;

        if (!programStructure || !programStructure.labSeries || programStructure.labSeries.length === 0) {
            treeContainer.innerHTML =
                '<div class="empty-state">' +
                '<p>No program structure yet.</p>' +
                '<p class="hint">Use the chat to generate a Lab Series and Labs structure from your objectives.</p>' +
                '</div>';
            _bindToolbarOnly();
            return;
        }

        // Auto-collapse labs within series if total lab count would overflow
        const totalLabs = programStructure.labSeries.reduce((sum, ls) => sum + (ls.labs || []).length, 0);
        const autoCollapseLabs = totalLabs > 8;

        treeContainer.innerHTML = _renderLabSeriesList(programStructure.labSeries, autoCollapseLabs);
        _bindOutlineEventsOnce();
        _bindToolbarOnly();
    }

    function _bindToolbarOnly() {
        const addSeriesBtn = $('#phase2-add-series');
        if (addSeriesBtn) addSeriesBtn.onclick = () => _addSeries();

        const expandBtn = $('#phase2-expand-all');
        if (expandBtn) expandBtn.onclick = () => expandAll();

        const collapseBtn = $('#phase2-collapse-all');
        if (collapseBtn) collapseBtn.onclick = () => collapseAll();
    }

    // ── Render helpers ───────────────────────────────────────────

    function _renderLabSeriesList(labSeriesList, autoCollapseLabs) {
        return labSeriesList.map((ls, lsIdx) => {
            const labs = ls.labs || [];
            const hasLabs = labs.length > 0;
            const totalLabs = labSeriesList.length;
            const collapsed = autoCollapseLabs ? ' collapsed' : '';
            const toggleChar = autoCollapseLabs ? '\u25B6' : '\u25BC';

            const labsHtml = hasLabs
                ? `<div class="outline-children${collapsed}">${labs.map((lab, labIdx) => _renderLab(lab, labIdx, labs.length, ls.id)).join('')}</div>`
                : '<div class="outline-children"></div>';

            return `
                <div class="outline-node" data-depth="0" data-type="lab-series" data-id="${ls.id || ''}">
                    <span class="outline-toggle">${hasLabs ? toggleChar : ''}</span>
                    <span class="outline-icon">\u{1F4DA}</span>
                    <span class="outline-title" contenteditable="true" data-node-type="labSeries" data-node-id="${ls.id || ''}">${_escHtml(ls.title || 'Untitled Series')}</span>
                    <span class="outline-count">${labs.length} lab${labs.length !== 1 ? 's' : ''}</span>
                    <span class="outline-actions">
                        ${lsIdx > 0 ? `<button class="outline-btn" data-action="move-up" data-id="${ls.id}" data-type="labSeries" title="Move up">\u25B2</button>` : ''}
                        ${lsIdx < totalLabs - 1 ? `<button class="outline-btn" data-action="move-down" data-id="${ls.id}" data-type="labSeries" title="Move down">\u25BC</button>` : ''}
                        <button class="outline-btn outline-btn-add" data-action="add-lab" data-parent-id="${ls.id}" title="Add Lab">+</button>
                        <button class="outline-btn outline-btn-del" data-action="delete" data-id="${ls.id}" data-type="labSeries" title="Delete">\u00D7</button>
                    </span>
                </div>
                ${labsHtml}
            `;
        }).join('');
    }

    function _renderLab(lab, labIdx, totalLabs, seriesId) {
        const activities = lab.activities || [];
        const hasActivities = activities.length > 0;
        const duration = lab.estimatedDuration ? `(${lab.estimatedDuration} min)` : '';

        const activitiesHtml = hasActivities
            ? `<div class="outline-children collapsed">${activities.map((act, actIdx) => _renderActivity(act, actIdx, activities.length, lab.id)).join('')}</div>`
            : '<div class="outline-children collapsed"></div>';

        return `
            <div class="outline-node" data-depth="1" data-type="lab" data-id="${lab.id || ''}" data-parent-id="${seriesId}">
                <span class="outline-toggle">${hasActivities ? '\u25B6' : ''}</span>
                <span class="outline-icon">\u{1F9EA}</span>
                <span class="outline-title" contenteditable="true" data-node-type="lab" data-node-id="${lab.id || ''}">${_escHtml(lab.title || 'Untitled Lab')}</span>
                <span class="outline-duration">${duration}</span>
                <span class="outline-actions">
                    ${labIdx > 0 ? `<button class="outline-btn" data-action="move-up" data-id="${lab.id}" data-type="lab" data-parent-id="${seriesId}" title="Move up">\u25B2</button>` : ''}
                    ${labIdx < totalLabs - 1 ? `<button class="outline-btn" data-action="move-down" data-id="${lab.id}" data-type="lab" data-parent-id="${seriesId}" title="Move down">\u25BC</button>` : ''}
                    <button class="outline-btn outline-btn-add" data-action="add-activity" data-parent-id="${lab.id}" title="Add Activity">+</button>
                    <button class="outline-btn outline-btn-del" data-action="delete" data-id="${lab.id}" data-type="lab" data-parent-id="${seriesId}" title="Delete">\u00D7</button>
                </span>
            </div>
            ${activitiesHtml}
        `;
    }

    function _renderActivity(activity, actIdx, totalActs, labId) {
        return `
            <div class="outline-node" data-depth="2" data-type="activity" data-id="${activity.id || ''}" data-parent-id="${labId}">
                <span class="outline-toggle"></span>
                <span class="outline-icon">\u{1F4CB}</span>
                <span class="outline-title" contenteditable="true" data-node-type="activity" data-node-id="${activity.id || ''}">${_escHtml(activity.title || 'Untitled Activity')}</span>
                <span class="outline-actions">
                    ${actIdx > 0 ? `<button class="outline-btn" data-action="move-up" data-id="${activity.id}" data-type="activity" data-parent-id="${labId}" title="Move up">\u25B2</button>` : ''}
                    ${actIdx < totalActs - 1 ? `<button class="outline-btn" data-action="move-down" data-id="${activity.id}" data-type="activity" data-parent-id="${labId}" title="Move down">\u25BC</button>` : ''}
                    <button class="outline-btn outline-btn-del" data-action="delete" data-id="${activity.id}" data-type="activity" data-parent-id="${labId}" title="Delete">\u00D7</button>
                </span>
            </div>
        `;
    }

    // ── Event binding ────────────────────────────────────────────

    function _bindOutlineEvents(container) {
        // Toggle expand/collapse
        container.addEventListener('click', (e) => {
            const toggle = e.target.closest('.outline-toggle');
            if (toggle) {
                const nodeEl = toggle.closest('.outline-node');
                if (nodeEl) toggleNode(nodeEl);
                return;
            }
            const icon = e.target.closest('.outline-icon');
            if (icon) {
                const nodeEl = icon.closest('.outline-node');
                if (nodeEl) toggleNode(nodeEl);
                return;
            }

            // Action buttons
            const actionBtn = e.target.closest('[data-action]');
            if (actionBtn) {
                e.stopPropagation();
                _handleAction(actionBtn);
                return;
            }
        });

        // Inline editing
        container.addEventListener('blur', (e) => {
            if (e.target.classList.contains('outline-title')) {
                _handleTitleEdit(e.target);
            }
        }, true);

        container.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('outline-title')) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    e.target.blur();
                } else if (e.key === 'Escape') {
                    if (e.target.dataset.original) {
                        e.target.textContent = e.target.dataset.original;
                    }
                    e.target.blur();
                }
            }
        });

        container.addEventListener('focus', (e) => {
            if (e.target.classList.contains('outline-title')) {
                e.target.dataset.original = e.target.textContent;
            }
        }, true);
    }

    // ── Action dispatcher ────────────────────────────────────────

    function _handleAction(btn) {
        const action = btn.dataset.action;
        const id = btn.dataset.id;
        const type = btn.dataset.type;
        const parentId = btn.dataset.parentId;

        switch (action) {
            case 'add-lab':     _addLab(parentId); break;
            case 'add-activity': _addActivity(parentId); break;
            case 'delete':      _deleteNode(type, id, parentId); break;
            case 'move-up':     _moveNode(type, id, parentId, -1); break;
            case 'move-down':   _moveNode(type, id, parentId, 1); break;
        }
    }

    // ── CRUD operations ──────────────────────────────────────────

    function _getProjectAndStructure() {
        const project = Store.getActiveProject();
        if (!project) return null;
        if (!project.programStructure) project.programStructure = { labSeries: [] };
        if (!project.programStructure.labSeries) project.programStructure.labSeries = [];
        return project;
    }

    function _saveAndRerender(project) {
        Store.updateProgramStructure(project.id, project.programStructure);
        renderOutline(project.programStructure);
    }

    function _addSeries() {
        const project = _getProjectAndStructure();
        if (!project) return;
        project.programStructure.labSeries.push({
            id: _genId(),
            title: 'New Lab Series',
            labs: [],
        });
        _saveAndRerender(project);
    }

    function _addLab(seriesId) {
        const project = _getProjectAndStructure();
        if (!project) return;
        const series = project.programStructure.labSeries.find(ls => ls.id === seriesId);
        if (!series) return;
        if (!series.labs) series.labs = [];
        series.labs.push({
            id: _genId(),
            title: 'New Lab',
            estimatedDuration: 45,
            activities: [],
        });
        _saveAndRerender(project);
    }

    function _addActivity(labId) {
        const project = _getProjectAndStructure();
        if (!project) return;
        for (const ls of project.programStructure.labSeries) {
            const lab = (ls.labs || []).find(l => l.id === labId);
            if (lab) {
                if (!lab.activities) lab.activities = [];
                lab.activities.push({
                    id: _genId(),
                    title: 'New Activity',
                });
                _saveAndRerender(project);
                return;
            }
        }
    }

    function _deleteNode(type, id, parentId) {
        const project = _getProjectAndStructure();
        if (!project) return;
        const structure = project.programStructure;

        if (type === 'labSeries') {
            structure.labSeries = structure.labSeries.filter(ls => ls.id !== id);
        } else if (type === 'lab') {
            const series = structure.labSeries.find(ls => ls.id === parentId);
            if (series) series.labs = (series.labs || []).filter(l => l.id !== id);
        } else if (type === 'activity') {
            for (const ls of structure.labSeries) {
                const lab = (ls.labs || []).find(l => l.id === parentId);
                if (lab) {
                    lab.activities = (lab.activities || []).filter(a => a.id !== id);
                    break;
                }
            }
        }
        _saveAndRerender(project);
    }

    function _moveNode(type, id, parentId, direction) {
        const project = _getProjectAndStructure();
        if (!project) return;
        const structure = project.programStructure;

        let arr;
        if (type === 'labSeries') {
            arr = structure.labSeries;
        } else if (type === 'lab') {
            const series = structure.labSeries.find(ls => ls.id === parentId);
            arr = series ? series.labs : null;
        } else if (type === 'activity') {
            for (const ls of structure.labSeries) {
                const lab = (ls.labs || []).find(l => l.id === parentId);
                if (lab) { arr = lab.activities; break; }
            }
        }

        if (!arr) return;
        const idx = arr.findIndex(item => item.id === id);
        const newIdx = idx + direction;
        if (idx < 0 || newIdx < 0 || newIdx >= arr.length) return;

        [arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]];
        _saveAndRerender(project);
    }

    // ── Inline title editing ─────────────────────────────────────

    function _handleTitleEdit(titleEl) {
        const newTitle = titleEl.textContent.trim();
        const oldTitle = titleEl.dataset.original || '';
        if (!newTitle || newTitle === oldTitle) {
            delete titleEl.dataset.original;
            return;
        }

        const project = Store.getActiveProject();
        if (!project || !project.programStructure) {
            delete titleEl.dataset.original;
            return;
        }

        const nodeType = titleEl.dataset.nodeType;
        const nodeId = titleEl.dataset.nodeId;

        if (nodeId) {
            _renameNodeById(project.programStructure, nodeType, nodeId, newTitle);
        } else {
            _renameNodeByTitle(project.programStructure, oldTitle, newTitle);
        }

        Store.updateProgramStructure(project.id, project.programStructure);
        delete titleEl.dataset.original;
    }

    function _renameNodeById(structure, nodeType, nodeId, newTitle) {
        if (!structure || !structure.labSeries) return;
        for (const ls of structure.labSeries) {
            if (nodeType === 'labSeries' && ls.id === nodeId) { ls.title = newTitle; return; }
            for (const lab of (ls.labs || [])) {
                if (nodeType === 'lab' && lab.id === nodeId) { lab.title = newTitle; return; }
                for (const act of (lab.activities || [])) {
                    if (nodeType === 'activity' && act.id === nodeId) { act.title = newTitle; return; }
                }
            }
        }
    }

    function _renameNodeByTitle(structure, oldTitle, newTitle) {
        if (!structure || !structure.labSeries) return;
        for (const ls of structure.labSeries) {
            if (ls.title === oldTitle) { ls.title = newTitle; return; }
            for (const lab of (ls.labs || [])) {
                if (lab.title === oldTitle) { lab.title = newTitle; return; }
                for (const act of (lab.activities || [])) {
                    if (act.title === oldTitle) { act.title = newTitle; return; }
                }
            }
        }
    }

    // ── Tree toggle operations ───────────────────────────────────

    function toggleNode(element) {
        const sibling = element.nextElementSibling;
        if (sibling && sibling.classList.contains('outline-children')) {
            sibling.classList.toggle('collapsed');
            const toggle = element.querySelector('.outline-toggle');
            if (toggle) {
                toggle.textContent = sibling.classList.contains('collapsed') ? '\u25B6' : '\u25BC';
            }
        }
    }

    function expandAll() {
        const container = $('#phase2-outline-tree');
        if (!container) return;
        $$('.outline-children', container).forEach(el => el.classList.remove('collapsed'));
        $$('.outline-toggle', container).forEach(el => {
            if (el.textContent.trim()) el.textContent = '\u25BC';
        });
    }

    function collapseAll() {
        const container = $('#phase2-outline-tree');
        if (!container) return;
        $$('.outline-children', container).forEach(el => el.classList.add('collapsed'));
        $$('.outline-toggle', container).forEach(el => {
            if (el.textContent.trim()) el.textContent = '\u25B6';
        });
    }

    // ══════════════════════════════════════════════════════════════
    //  Tab 2: Skill Mapping (AI-auto with approve / override)
    // ══════════════════════════════════════════════════════════════

    function renderSkillMapping(project) {
        const content = $('#phase2-framework-content');
        if (!content) return;

        const competencies = project.competencies || [];
        const structure = project.programStructure;
        const hasStructure = structure && structure.labSeries && structure.labSeries.length > 0;
        const mappings = project.skillMappings || [];

        // Framework selector
        const frameworks = typeof Frameworks !== 'undefined' ? Frameworks.getAll() : [];
        const domains = typeof Frameworks !== 'undefined' ? Frameworks.getDomains() : {};
        const selectedId = project.framework || '';

        let optionsHtml = '<option value="">None (Skip)</option>';
        for (const [domain, fws] of Object.entries(domains)) {
            optionsHtml += `<optgroup label="${_escHtml(domain)}">`;
            fws.forEach(fw => {
                const sel = fw.id === selectedId ? ' selected' : '';
                optionsHtml += `<option value="${fw.id}"${sel}>${_escHtml(fw.name)}</option>`;
            });
            optionsHtml += '</optgroup>';
        }

        // Build the target list (activities and labs) for mapping dropdowns
        const targets = _buildMappingTargets(structure);

        // If we have competencies but no mappings yet, show the auto-map prompt
        let mappingsHtml = '';
        if (competencies.length === 0) {
            mappingsHtml = `
                <div class="empty-state" style="margin-top:16px;">
                    <p>No competencies defined yet.</p>
                    <p class="hint">Complete Phase 1 to extract competencies from your objectives and uploads.</p>
                </div>
            `;
        } else if (!hasStructure) {
            mappingsHtml = `
                <div class="empty-state" style="margin-top:16px;">
                    <p>No lab outline yet.</p>
                    <p class="hint">Generate an outline in the Lab Outline tab first, then come back to map skills.</p>
                </div>
            `;
        } else if (mappings.length === 0) {
            mappingsHtml = `
                <div class="skill-map-prompt" style="margin-top:16px;">
                    <p style="font-size:13px;color:var(--color-text-secondary);margin-bottom:8px;">
                        You have <strong>${competencies.length}</strong> competencies and <strong>${targets.length}</strong> mappable items in your outline.
                    </p>
                    <button id="phase2-auto-map" class="btn btn-primary btn-sm">Auto-Map Skills</button>
                    <p class="hint" style="margin-top:6px;">AI will recommend where each competency maps. You can approve or override each one.</p>
                </div>
            `;
        } else {
            mappingsHtml = `
                <div class="skill-map-header" style="margin-top:12px;">
                    <span style="font-size:12px;color:var(--color-text-muted);">${_countApproved(mappings)} of ${mappings.length} approved</span>
                    <button id="phase2-approve-all" class="btn-sm" style="margin-left:8px;">Approve All</button>
                    <button id="phase2-remap" class="btn-sm" style="margin-left:4px;">Re-Map</button>
                </div>
                <div id="phase2-mappings-list" style="margin-top:8px;">
                    ${mappings.map((m, i) => _renderMappingRow(m, i, targets)).join('')}
                </div>
            `;
        }

        content.innerHTML = `
            <div class="form-group">
                <label class="form-label">Skill Framework</label>
                <select id="phase2-framework-select" class="form-select">${optionsHtml}</select>
            </div>
            <div class="form-group" style="margin-top:8px;">
                <label class="form-label">Or upload a custom framework</label>
                <input type="file" id="phase2-framework-upload" accept=".json,.csv,.txt" class="form-input" />
            </div>
            ${mappingsHtml}
        `;

        // Bind skill mapping events once on the persistent content element.
        // Store current project/targets so the delegated handler always has fresh data.
        _currentMappingProject = project;
        _currentMappingTargets = targets;
        _bindSkillMappingEventsOnce(content);
    }

    function _buildMappingTargets(structure) {
        const targets = [];
        if (!structure || !structure.labSeries) return targets;
        for (const ls of structure.labSeries) {
            for (const lab of (ls.labs || [])) {
                targets.push({ id: lab.id, label: lab.title, type: 'lab', icon: '\u{1F9EA}' });
                for (const act of (lab.activities || [])) {
                    targets.push({ id: act.id, label: `${act.title}`, type: 'activity', icon: '\u{1F4CB}', parentLab: lab.title });
                }
            }
        }
        return targets;
    }

    function _renderMappingRow(mapping, index, targets) {
        const approved = mapping.approved;
        const statusClass = approved ? 'mapping-approved' : 'mapping-pending';
        const statusLabel = approved ? 'Approved' : 'Pending';
        const levelLabel = mapping.level === 'activity' ? 'Activity' : 'Lab';

        let targetSelect = `<select class="mapping-target-select" data-mapping-idx="${index}">`;
        targetSelect += `<option value="">-- Select target --</option>`;
        for (const t of targets) {
            const indent = t.type === 'activity' ? '\u00A0\u00A0\u00A0\u00A0' : '';
            const icon = t.type === 'activity' ? '\u{1F4CB}' : '\u{1F9EA}';
            const sel = (mapping.targetId === t.id) ? ' selected' : '';
            targetSelect += `<option value="${t.id}" data-type="${t.type}"${sel}>${indent}${icon} ${_escHtml(t.label)}</option>`;
        }
        targetSelect += '</select>';

        return `
            <div class="mapping-row ${statusClass}" data-mapping-idx="${index}">
                <div class="mapping-target">
                    <span class="mapping-dot ${approved ? 'filled' : ''}"></span>
                    ${targetSelect}
                    <span class="mapping-level">${levelLabel}</span>
                </div>
                <div class="mapping-arrow">\u2192</div>
                <div class="mapping-competency">
                    <strong>${_escHtml(mapping.competency)}</strong>
                    ${mapping.source ? `<span class="mapping-source">[${_escHtml(mapping.source)}]</span>` : ''}
                </div>
                <div class="mapping-actions">
                    ${!approved
                        ? `<button class="btn-sm mapping-approve-btn" data-mapping-idx="${index}" title="Approve">\u2713</button>`
                        : `<button class="btn-sm mapping-unapprove-btn" data-mapping-idx="${index}" title="Undo approval">\u21A9</button>`
                    }
                </div>
            </div>
        `;
    }

    // _bindMappingActions removed — logic consolidated into _bindSkillMappingEventsOnce()

    function _autoMapSkills(project, targets) {
        // Client-side heuristic auto-mapping: match competency names to activity/lab titles
        // In production, this would call the AI API for intelligent mapping
        const competencies = project.competencies || [];
        const mappings = [];

        for (const comp of competencies) {
            const compWords = (comp.name || '').toLowerCase().split(/\s+/);
            let bestTarget = null;
            let bestScore = 0;
            let bestLevel = 'lab';

            for (const target of targets) {
                const titleWords = (target.label || '').toLowerCase().split(/\s+/);
                let score = 0;
                for (const w of compWords) {
                    if (w.length < 3) continue;
                    for (const tw of titleWords) {
                        if (tw.includes(w) || w.includes(tw)) score++;
                    }
                }
                if (score > bestScore) {
                    bestScore = score;
                    bestTarget = target;
                    bestLevel = target.type;
                }
            }

            // If no good match, default to first lab
            if (!bestTarget && targets.length > 0) {
                bestTarget = targets.find(t => t.type === 'lab') || targets[0];
                bestLevel = bestTarget.type;
            }

            mappings.push({
                competencyId: comp.id,
                competency: comp.name,
                source: comp.source || '',
                targetId: bestTarget ? bestTarget.id : '',
                targetLabel: bestTarget ? bestTarget.label : '',
                level: bestLevel,
                approved: false,
            });
        }

        project.skillMappings = mappings;
        Store.updateProject(project);
        renderSkillMapping(project);
    }

    function _setMappingApproved(projectId, idx, approved) {
        const project = Store.getProject(projectId);
        if (!project || !project.skillMappings || !project.skillMappings[idx]) return;
        project.skillMappings[idx].approved = approved;
        Store.updateProject(project);
        renderSkillMapping(project);
    }

    function _updateMappingTarget(projectId, idx, targetId, targetType) {
        const project = Store.getProject(projectId);
        if (!project || !project.skillMappings || !project.skillMappings[idx]) return;
        project.skillMappings[idx].targetId = targetId;
        project.skillMappings[idx].level = targetType || 'lab';
        // Reset approval when target changes
        project.skillMappings[idx].approved = false;
        Store.updateProject(project);
        renderSkillMapping(project);
    }

    function _approveAll(projectId) {
        const project = Store.getProject(projectId);
        if (!project || !project.skillMappings) return;
        project.skillMappings.forEach(m => m.approved = true);
        Store.updateProject(project);
        renderSkillMapping(project);
    }

    function _countApproved(mappings) {
        return mappings.filter(m => m.approved).length;
    }

    function handleFrameworkSelect(frameworkId, projectId) {
        const project = Store.getProject(projectId);
        if (!project) return;
        project.framework = frameworkId || null;
        if (!frameworkId) project.frameworkData = null;
        Store.updateProject(project);
        renderSkillMapping(project);
    }

    function handleFrameworkUpload(file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            try {
                const ext = file.name.split('.').pop().toLowerCase();
                const parsed = Frameworks.parseUploadedFramework(ev.target.result, ext);
                const customId = 'custom-' + Date.now();
                const registered = Frameworks.registerCustom({
                    id: customId,
                    name: parsed.name || file.name,
                    organization: 'Custom Upload',
                    domain: 'Custom',
                    description: `Uploaded from ${file.name}`,
                    competencies: parsed.competencies || [],
                });

                const project = Store.getActiveProject();
                if (project) {
                    project.framework = registered.id;
                    project.frameworkData = {
                        name: parsed.name || file.name,
                        competencies: parsed.competencies || [],
                        source: 'upload',
                    };
                    Store.updateProject(project);
                    renderSkillMapping(project);
                }
            } catch (err) {
                console.error('[Phase2] Framework upload parse error:', err);
                alert('Could not parse framework file: ' + err.message);
            }
        };
        reader.readAsText(file);
    }

    // ── AI Results Integration ───────────────────────────────────

    function applyAIResults(structured, projectId) {
        if (!structured || !projectId) return;

        Store.updateProgramStructure(projectId, structured);

        if (structured.instructionStyle) {
            Store.setInstructionStyle(projectId, structured.instructionStyle);
        }

        renderOutline(structured);
    }

    // ── Context Summary ──────────────────────────────────────────

    function getContextSummary(projectId) {
        const project = Store.getProject(projectId);
        if (!project) return 'No project data available.';

        const lines = [];
        lines.push('## Phase 2: Design & Organize Summary');
        lines.push('');

        if (project.programStructure && project.programStructure.labSeries) {
            lines.push('### Program Outline');
            for (const ls of project.programStructure.labSeries) {
                lines.push(`- [Lab Series] ${ls.title || 'Untitled'}`);
                for (const lab of (ls.labs || [])) {
                    const dur = lab.estimatedDuration ? ` (${lab.estimatedDuration} min)` : '';
                    lines.push(`  - [Lab] ${lab.title || 'Untitled'}${dur}`);
                    for (const act of (lab.activities || [])) {
                        lines.push(`    - [Activity] ${act.title || 'Untitled'}`);
                    }
                }
            }
            lines.push('');
        } else {
            lines.push('### Program Structure: Not yet defined');
            lines.push('');
        }

        if (project.framework) {
            const fw = typeof Frameworks !== 'undefined' ? Frameworks.getById(project.framework) : null;
            if (fw) {
                lines.push(`### Framework: ${fw.name} (${fw.publisher})`);
            } else {
                lines.push(`### Framework: ${project.framework}`);
            }
            lines.push('');
        }

        if (project.skillMappings && project.skillMappings.length > 0) {
            lines.push('### Skill Mappings');
            project.skillMappings.forEach(m => {
                const status = m.approved ? '\u2713' : '?';
                lines.push(`  ${status} ${m.competency} \u2192 ${m.targetLabel || 'unmapped'} (${m.level})`);
            });
            lines.push('');
        }

        const seatTime = project.seatTime || { min: 45, max: 90 };
        lines.push('### Lab Settings');
        lines.push(`- Seat time: ${seatTime.min}\u2013${seatTime.max} minutes`);
        if (project.instructionStyle) {
            lines.push(`- Instruction style: ${project.instructionStyle}`);
        }
        lines.push('');

        return lines.join('\n');
    }

    // ── Utilities ────────────────────────────────────────────────

    function _escHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ── Public API ───────────────────────────────────────────────

    return {
        init,
        render,
        renderOutline,
        renderSkillMapping,
        toggleNode,
        expandAll,
        collapseAll,
        applyAIResults,
        handleFrameworkSelect,
        handleFrameworkUpload,
        getContextSummary,
    };
})();
