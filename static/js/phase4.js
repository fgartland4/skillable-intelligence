/**
 * phase4.js — Phase 4 "Package & Export" UI controller for Lab Program Designer v3.
 *
 * Conversational flow: AI analyzes Phases 1-3, generates an environment checklist,
 * asks context-specific clarifying questions, and lets the designer confirm/adjust.
 *
 * Right panel: two tabs
 *   - Environment Checklist (live, categorized, updated via conversation)
 *   - Export (package for Skillable Studio)
 *
 * Depends on: Store, Chat (all global IIFEs).
 */

const Phase4 = (() => {

    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)];

    function _esc(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    }

    // ── Checklist Categories ──────────────────────────────────────

    const CATEGORIES = [
        { id: 'cloud', label: 'Cloud & Subscriptions', icon: '\u2601' },
        { id: 'vms', label: 'Virtual Machines', icon: '\u{1F5A5}' },
        { id: 'containers', label: 'Containers & IDEs', icon: '\u{1F4E6}' },
        { id: 'software', label: 'Software & Tools', icon: '\u{1F527}' },
        { id: 'accounts', label: 'Accounts & Credentials', icon: '\u{1F511}' },
        { id: 'data', label: 'Data & Files', icon: '\u{1F4C4}' },
        { id: 'network', label: 'Networking & Permissions', icon: '\u{1F310}' },
        { id: 'scripts', label: 'Lifecycle Scripts', icon: '\u{1F4DC}' },
        { id: 'scoring', label: 'Scoring & Assessment', icon: '\u2705' },
        { id: 'other', label: 'Other', icon: '\u{1F4CB}' },
    ];

    // ── Init ─────────────────────────────────────────────────────

    function _getContainer() {
        return $('#phase4-context .center-pane-body') || $('#phase4-context');
    }

    function init() {
        const container = _getContainer();
        if (!container) return;

        container.addEventListener('click', (e) => {
            const target = e.target;

            // Tab switching
            const tabBtn = target.closest('[data-phase4-tab]');
            if (tabBtn) {
                const tabName = tabBtn.dataset.phase4Tab;
                $$('[data-phase4-tab]', container).forEach(b => b.classList.remove('active'));
                tabBtn.classList.add('active');
                $$('.phase4-tab-panel', container).forEach(p => {
                    p.style.display = 'none';
                    p.classList.remove('active');
                });
                const panel = $(`#phase4-tab-${tabName}`, container);
                if (panel) {
                    panel.style.display = '';
                    panel.classList.add('active');
                }
                return;
            }

            // Toggle checklist item status
            const checkItem = target.closest('.checklist-item-toggle');
            if (checkItem) {
                const itemId = checkItem.dataset.itemId;
                const projectId = checkItem.dataset.projectId;
                _toggleItemStatus(projectId, itemId);
                return;
            }

            // Delete checklist item
            const deleteItem = target.closest('.checklist-item-delete');
            if (deleteItem) {
                const itemId = deleteItem.dataset.itemId;
                const projectId = deleteItem.dataset.projectId;
                _deleteItem(projectId, itemId);
                return;
            }

            // Export buttons
            const exportBtn = target.closest('#btn-export-skillable');
            if (exportBtn) {
                handleExport(exportBtn.dataset.projectId);
                return;
            }

            const jsonBtn = target.closest('#btn-export-json');
            if (jsonBtn) {
                handleExportJSON(jsonBtn.dataset.projectId);
                return;
            }
        });
    }

    // ── Render ────────────────────────────────────────────────────

    function render(project) {
        const container = _getContainer();
        if (!container || !project) return;

        const programName = (project.name && project.name !== 'Untitled Program') ? project.name : '';
        const checklist = project.environmentChecklist || [];

        const checklistHtml = _renderChecklist(checklist, project.id);
        const exportHtml = _renderExport(project);

        container.innerHTML = `
            <div class="bp-header">
                <h3 class="bp-title">Lab Blueprint</h3>
                ${programName ? `<div class="bp-program-name">${_esc(programName)}</div>` : ''}
            </div>

            <div class="phase2-tabs">
                <button class="context-tab active" data-phase4-tab="checklist">Environment Checklist</button>
                <button class="context-tab" data-phase4-tab="export">Export</button>
            </div>

            <div id="phase4-tab-checklist" class="phase4-tab-panel phase3-tab-panel active">
                ${checklistHtml}
            </div>

            <div id="phase4-tab-export" class="phase4-tab-panel phase3-tab-panel" style="display:none;padding:12px 16px;">
                ${exportHtml}
            </div>
        `;
    }

    // ── Checklist Rendering ───────────────────────────────────────

    function _renderChecklist(checklist, projectId) {
        if (!checklist || checklist.length === 0) {
            return `
                <div class="phase3-empty-state">
                    <p>No environment checklist yet.</p>
                    <p class="hint">The AI will build this as you discuss environment needs in chat.</p>
                </div>
            `;
        }

        // Group items by category
        const grouped = {};
        for (const item of checklist) {
            const cat = item.category || 'other';
            if (!grouped[cat]) grouped[cat] = [];
            grouped[cat].push(item);
        }

        // Count stats
        const total = checklist.length;
        const confirmed = checklist.filter(i => i.status === 'confirmed').length;

        let html = `
            <div class="checklist-summary">
                <span class="checklist-stat">${confirmed}/${total} confirmed</span>
            </div>
        `;

        for (const catDef of CATEGORIES) {
            const items = grouped[catDef.id];
            if (!items || items.length === 0) continue;

            html += `
                <div class="checklist-category">
                    <div class="checklist-category-header">
                        <span class="checklist-category-icon">${catDef.icon}</span>
                        <span class="checklist-category-label">${catDef.label}</span>
                        <span class="checklist-category-count">${items.length}</span>
                    </div>
                    <div class="checklist-items">
                        ${items.map(item => _renderChecklistItem(item, projectId)).join('')}
                    </div>
                </div>
            `;
        }

        return html;
    }

    function _renderChecklistItem(item, projectId) {
        const isConfirmed = item.status === 'confirmed';
        const statusIcon = isConfirmed ? '\u2705' : '\u26AA';
        const statusClass = isConfirmed ? 'confirmed' : 'pending';

        return `
            <div class="checklist-item ${statusClass}">
                <span class="checklist-item-toggle" data-item-id="${item.id}" data-project-id="${projectId}" title="${isConfirmed ? 'Mark as pending' : 'Confirm'}">
                    ${statusIcon}
                </span>
                <div class="checklist-item-content">
                    <span class="checklist-item-name">${_esc(item.name)}</span>
                    ${item.details ? `<span class="checklist-item-details">${_esc(item.details)}</span>` : ''}
                    ${item.labRef ? `<span class="checklist-item-lab-ref">${_esc(item.labRef)}</span>` : ''}
                </div>
                <button class="checklist-item-delete" data-item-id="${item.id}" data-project-id="${projectId}" title="Remove">&times;</button>
            </div>
        `;
    }

    // ── Export Rendering ──────────────────────────────────────────

    function _renderExport(project) {
        const structure = project.programStructure;
        let labList = [];
        if (structure && structure.labSeries) {
            for (const ls of structure.labSeries) {
                for (const lab of (ls.labs || [])) {
                    labList.push({ id: lab.id, title: lab.title, seriesTitle: ls.title });
                }
            }
        }

        const checklist = project.environmentChecklist || [];
        const totalItems = checklist.length;
        const confirmedItems = checklist.filter(i => i.status === 'confirmed').length;
        const hasDrafts = project.draftInstructions && Object.keys(project.draftInstructions).length > 0;

        // Readiness indicators
        const readiness = [];
        if (labList.length > 0) readiness.push({ label: 'Lab structure', ok: true });
        else readiness.push({ label: 'Lab structure', ok: false, hint: 'Complete Phase 2' });

        if (hasDrafts) readiness.push({ label: 'Draft instructions', ok: true });
        else readiness.push({ label: 'Draft instructions', ok: false, hint: 'Complete Phase 3' });

        if (totalItems > 0 && confirmedItems === totalItems) readiness.push({ label: 'Environment checklist', ok: true });
        else if (totalItems > 0) readiness.push({ label: 'Environment checklist', ok: false, hint: `${confirmedItems}/${totalItems} confirmed` });
        else readiness.push({ label: 'Environment checklist', ok: false, hint: 'Not started' });

        const readinessHtml = readiness.map(r => `
            <div class="export-readiness-item ${r.ok ? 'ready' : 'not-ready'}">
                <span class="export-readiness-icon">${r.ok ? '\u2705' : '\u26AA'}</span>
                <span class="export-readiness-label">${r.label}</span>
                ${r.hint ? `<span class="export-readiness-hint">${r.hint}</span>` : ''}
            </div>
        `).join('');

        const checkboxes = labList.map(lab => `
            <label class="export-lab-checkbox">
                <input type="checkbox" value="${lab.id}" checked />
                ${_esc(lab.title)}
                ${lab.seriesTitle ? `<span class="export-series-tag">${_esc(lab.seriesTitle)}</span>` : ''}
            </label>`).join('');

        return `
            <div class="export-section">
                <h4 class="export-heading">Export Readiness</h4>
                <div class="export-readiness">${readinessHtml}</div>
            </div>

            ${labList.length > 0 ? `
            <div class="export-section" style="margin-top:16px;">
                <h4 class="export-heading">Labs to Include</h4>
                <div class="export-checkboxes">${checkboxes}</div>
            </div>
            <div class="export-actions" style="margin-top:16px;">
                <button class="btn btn-primary" id="btn-export-skillable" data-project-id="${project.id}">Export to Skillable Studio</button>
                <button class="btn btn-secondary" id="btn-export-json" data-project-id="${project.id}">Export as JSON</button>
            </div>` : `
            <p class="hint" style="margin-top:12px;">Complete Phases 2 and 3 before exporting.</p>`}
        `;
    }

    // ── Checklist Mutations ───────────────────────────────────────

    function _toggleItemStatus(projectId, itemId) {
        const project = Store.getProject(projectId);
        if (!project || !project.environmentChecklist) return;
        const item = project.environmentChecklist.find(i => i.id === itemId);
        if (item) {
            item.status = item.status === 'confirmed' ? 'pending' : 'confirmed';
            Store.updateProject(project);
            render(project);
        }
    }

    function _deleteItem(projectId, itemId) {
        const project = Store.getProject(projectId);
        if (!project || !project.environmentChecklist) return;
        project.environmentChecklist = project.environmentChecklist.filter(i => i.id !== itemId);
        Store.updateProject(project);
        render(project);
    }

    // ── AI Results Integration ────────────────────────────────────

    function applyAIResults(structured, projectId) {
        if (!structured) return;
        const project = Store.getProject(projectId);
        if (!project) return;

        // Handle checklist items from AI
        if (Array.isArray(structured.checklistItems)) {
            if (!project.environmentChecklist) project.environmentChecklist = [];
            for (const item of structured.checklistItems) {
                project.environmentChecklist.push({
                    id: item.id || Store.generateId(),
                    category: item.category || 'other',
                    name: item.name || '',
                    details: item.details || '',
                    labRef: item.labRef || '',
                    status: item.status || 'pending',
                });
            }
            Store.updateProject(project);
        }

        render(Store.getProject(projectId));
    }

    // ── Export Handlers ───────────────────────────────────────────

    async function handleExport(projectId) {
        const project = Store.getProject(projectId);
        if (!project) return;

        const checkboxes = document.querySelectorAll('.export-lab-checkbox input[type="checkbox"]:checked');
        const selectedIds = Array.from(checkboxes).map(cb => cb.value);
        if (selectedIds.length === 0) { alert('Select at least one lab.'); return; }

        try {
            if (typeof Exporter !== 'undefined') {
                await Exporter.exportToSkillable(project, { labIds: selectedIds });
            }
            Store.addExportRecord(projectId, { format: 'Skillable ZIP', labCount: selectedIds.length });
            render(Store.getProject(projectId));
        } catch (err) {
            console.error('[Phase4] Export failed:', err);
            alert('Export failed: ' + err.message);
        }
    }

    function handleExportJSON(projectId) {
        const project = Store.getProject(projectId);
        if (!project) return;

        const json = JSON.stringify(project, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${_sanitizeFilename(project.name)}-project.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function _sanitizeFilename(name) {
        return (name || 'export').replace(/[^a-zA-Z0-9\s\-_]/g, '').replace(/\s+/g, '-').trim().slice(0, 80);
    }

    // ── Context Summary ──────────────────────────────────────────

    function getContextSummary(projectId) {
        const project = Store.getProject(projectId);
        if (!project) return '';
        const checklist = project.environmentChecklist || [];
        const confirmed = checklist.filter(i => i.status === 'confirmed').length;
        return `Phase 4 — Package & Export\nEnvironment checklist: ${confirmed}/${checklist.length} confirmed`;
    }

    // ── Public API ───────────────────────────────────────────────

    return {
        init,
        render,
        applyAIResults,
        getContextSummary,
        handleExport,
    };
})();
