/**
 * phase1.js — Phase 1 "Audiences & Objectives" UI controller.
 * Manages the split-panel layout: chat (left) + context panel (right).
 *
 * Context panel sections:
 *   - Uploaded Materials
 *   - Target Audiences
 *   - Business & Learning Objectives
 *   - Success Criteria
 *   - Technology & Platform
 *   - Documentation & References
 *   - Scenario Seeds
 *   - Competencies
 *
 * Depends on: Store (global IIFE).
 */

const Phase1 = (() => {

    // ── Utilities ───────────────────────────────────────────────

    function escHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDate(isoStr) {
        if (!isoStr) return '';
        try {
            const d = new Date(isoStr);
            return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        } catch {
            return '';
        }
    }

    function $(sel, ctx) {
        return (ctx || document).querySelector(sel);
    }

    function $$(sel, ctx) {
        return [...(ctx || document).querySelectorAll(sel)];
    }

    // ── Initialization ──────────────────────────────────────────

    function init() {
        _bindUploadButton();
        _bindAddUrlButton();
        _bindFileInput();
        _bindResetButton();
    }

    function _bindResetButton() {
        const btn = $('#phase1-reset-btn');
        if (!btn) return;
        btn.addEventListener('click', () => _showResetDialog());
    }

    function _bindUploadButton() {
        const container = $('#phase1-context');
        if (!container) return;

        container.addEventListener('click', (e) => {
            const uploadBtn = e.target.closest('[data-action="trigger-upload"]');
            if (uploadBtn) {
                const fileInput = $('#phase1-file-input');
                if (fileInput) fileInput.click();
            }
        });
    }

    function _showResetDialog() {
        // Remove any existing dialog
        const existing = document.getElementById('phase1-reset-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'phase1-reset-overlay';
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal reset-modal">
                <div class="modal-body reset-modal-body">
                    <div class="reset-modal-icon">🧹</div>
                    <h3 class="reset-modal-title">Clean slate?</h3>
                    <p class="reset-modal-text">
                        This will wipe everything in Phase 1 — your chat history,
                        the Blueprint, uploaded materials, all of it.
                        Like it never happened.
                    </p>
                    <p class="reset-modal-subtext">
                        (Phases 2–4 won't be touched.)
                    </p>
                </div>
                <div class="modal-footer reset-modal-footer">
                    <button class="btn-reset-cancel" id="reset-keep-going">Nah, keep going</button>
                    <button class="btn-reset-confirm" id="reset-nuke-it">Delete &amp; start over</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });

        // Keep going
        document.getElementById('reset-keep-going').addEventListener('click', () => {
            overlay.remove();
        });

        // Nuke it
        document.getElementById('reset-nuke-it').addEventListener('click', () => {
            _resetPhase1();
            overlay.remove();
        });
    }

    function _resetPhase1() {
        const pid = window.App ? App.getCurrentProjectId() : null;
        const project = pid ? Store.getProject(pid) : null;
        if (!project) return;

        // Clear all Phase 1 data
        project.uploads = [];
        project.urls = [];
        project.audiences = [];
        project.businessObjectives = [];
        project.learningObjectives = [];
        project.competencies = [];
        project.successCriteria = [];
        project.technologyPlatform = '';
        project.documentationRefs = [];
        project.scenarioSeeds = [];
        project.phase1Chat = [];
        project.recommendedDifficulty = '';
        project.recommendedFramework = null;
        project.name = 'Untitled Program';

        Store.updateProject(project);

        // Refresh app's reference to the project
        if (window.App && App.refreshCurrentProject) {
            App.refreshCurrentProject();
        }

        // Clear the chat DOM and show the welcome message
        const chatContainer = $('#phase1-chat-messages');
        if (chatContainer) chatContainer.innerHTML = '';
        if (window.App && App.showWelcomeIfNeeded) {
            App.showWelcomeIfNeeded();
        }

        // Re-render the Blueprint as empty state
        const container = $('#phase1-context');
        if (container) {
            container.innerHTML = `<div class="empty-state"><p>Upload materials or chat to get started.</p></div>`;
        }
    }

    function _bindAddUrlButton() {
        const container = $('#phase1-context');
        if (!container) return;

        container.addEventListener('click', (e) => {
            const addUrlBtn = e.target.closest('[data-action="add-url"]');
            if (addUrlBtn) {
                _showUrlInput(addUrlBtn);
            }
        });
    }

    function _bindFileInput() {
        const fileInput = $('#phase1-file-input');
        if (!fileInput) return;

        fileInput.addEventListener('change', (e) => {
            const project = Store.getActiveProject();
            if (!project) return;

            Array.from(e.target.files).forEach(file => {
                handleUpload(file, project.id);
            });
            e.target.value = '';
        });
    }

    function _showUrlInput(triggerBtn) {
        const existing = $('#phase1-url-input-row');
        if (existing) {
            existing.remove();
            return;
        }

        const row = document.createElement('div');
        row.id = 'phase1-url-input-row';
        row.className = 'url-input-row';
        row.innerHTML = `
            <input type="url" class="url-input-field" placeholder="https://example.com/document" />
            <button class="url-input-submit" title="Add URL">Add</button>
            <button class="url-input-cancel" title="Cancel">&times;</button>
        `;

        triggerBtn.parentElement.insertAdjacentElement('afterend', row);

        const input = row.querySelector('.url-input-field');
        const submitBtn = row.querySelector('.url-input-submit');
        const cancelBtn = row.querySelector('.url-input-cancel');

        input.focus();

        const submit = () => {
            const url = input.value.trim();
            if (!url) return;
            const project = Store.getActiveProject();
            if (!project) return;
            handleAddUrl(url, project.id);
            row.remove();
        };

        submitBtn.addEventListener('click', submit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') submit();
            if (e.key === 'Escape') row.remove();
        });
        cancelBtn.addEventListener('click', () => row.remove());
    }

    // ── Collapsible checklist state (persists within session) ───
    const _expandedSections = new Set();

    // ── Render: full context panel (collapsible checklist) ──────

    function render(project) {
        const container = $('#phase1-context');
        if (!container) return;

        container.innerHTML = '';

        // Gather counts for each section
        const uploads = project.uploads || [];
        const urls = project.urls || [];
        const audiences = project.audiences || [];
        const bizObj = project.businessObjectives || [];
        const learnObj = project.learningObjectives || [];
        const criteria = project.successCriteria || [];
        const docRefs = project.documentationRefs || [];
        const seeds = project.scenarioSeeds || [];
        const competencies = project.competencies || [];
        const platform = project.technologyPlatform || '';
        const seatTime = project.seatTime || { min: 45, max: 90 };
        const difficulty = project.recommendedDifficulty || '';
        const recFramework = project.recommendedFramework || null;

        // Blueprint header
        const programName = (project.name && project.name !== 'Untitled Program') ? project.name : '';
        container.innerHTML = `
            <div class="bp-header">
                <h3 class="bp-title">Lab Blueprint</h3>
                ${programName ? `<div class="bp-program-name">${escHtml(programName)}</div>` : ''}
            </div>
            <div class="bp-checklist" id="bp-checklist"></div>
        `;

        const checklist = $('#bp-checklist', container);

        // Define all checklist items
        const sections = [
            {
                key: 'objectives',
                label: 'Business / Learning Objectives',
                filled: bizObj.length > 0 || learnObj.length > 0,
                summary: _objectivesSummary(bizObj, learnObj),
                detail: (bizObj.length > 0 || learnObj.length > 0) ? _renderObjectivesDetail(bizObj, learnObj, project.id) : null,
            },
            {
                key: 'audiences',
                label: 'Target Audience(s)',
                filled: audiences.length > 0,
                summary: audiences.length > 0 ? `${audiences.length} defined` : 'None yet',
                detail: audiences.length > 0 ? _renderAudienceDetail(audiences) : null,
            },
            {
                key: 'platform',
                label: 'Primary Product / Platform',
                filled: !!platform,
                summary: platform || 'Not specified',
                detail: platform ? `<div class="bp-badge">${escHtml(platform)}</div>` : null,
            },
            {
                key: 'difficulty',
                label: 'Recommended Difficulty',
                filled: !!difficulty,
                summary: difficulty ? difficulty.charAt(0).toUpperCase() + difficulty.slice(1) : 'Pending',
                detail: null,
            },
            {
                key: 'seat-time',
                label: 'Target Lab Duration',
                filled: true, // always has a default
                summary: `${seatTime.min}\u2013${seatTime.max} min`,
                detail: _renderSeatTimeEditor(seatTime, project.id),
            },
            {
                key: 'criteria',
                label: 'Success Criteria',
                filled: criteria.length > 0,
                summary: criteria.length > 0 ? `${criteria.length} defined` : 'None yet',
                detail: criteria.length > 0 ? _renderListDetail(criteria) : null,
            },
            {
                key: 'scenarios',
                label: 'Scenario Seeds',
                filled: seeds.length > 0,
                summary: seeds.length > 0 ? `${seeds.length} ideas` : 'None yet',
                detail: seeds.length > 0 ? _renderSeedsDetail(seeds) : null,
            },
            {
                key: 'competencies',
                label: 'Competency Framework',
                filled: competencies.length > 0 || !!recFramework,
                summary: _competenciesSummary(competencies, recFramework),
                detail: (competencies.length > 0 || recFramework) ? _renderCompetenciesDetail(competencies, recFramework, project.id) : null,
            },
        ];

        for (const sec of sections) {
            const isExpanded = _expandedSections.has(sec.key);
            const hasDetail = !!sec.detail;
            const statusIcon = `<span class="bp-circle ${sec.filled ? 'filled' : ''}"></span>`;
            const chevron = hasDetail ? `<span class="bp-chevron ${isExpanded ? 'open' : ''}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg></span>` : '';

            const row = document.createElement('div');
            row.className = `bp-item ${sec.filled ? 'filled' : 'empty'}`;
            row.dataset.key = sec.key;
            row.innerHTML = `
                <div class="bp-item-header" ${hasDetail ? 'data-toggle-bp' : ''} data-key="${sec.key}">
                    <span class="bp-status">${statusIcon}</span>
                    <span class="bp-label">${sec.label}</span>
                    <span class="bp-summary">${sec.summary}</span>
                    ${chevron}
                </div>
                ${hasDetail ? `<div class="bp-item-detail" style="display:${isExpanded ? 'block' : 'none'};">${sec.detail}</div>` : ''}
            `;
            checklist.appendChild(row);
        }

        // Bind expand/collapse
        checklist.addEventListener('click', (e) => {
            // Framework accept/ignore buttons
            const fwBtn = e.target.closest('[data-action]');
            if (fwBtn) {
                const action = fwBtn.dataset.action;
                const pid = fwBtn.dataset.project;
                const proj = Store.getProject(pid);
                if (proj && proj.recommendedFramework) {
                    if (action === 'accept-framework') {
                        proj.recommendedFramework.accepted = true;
                        Store.updateProject(proj);
                        render(proj);
                    } else if (action === 'ignore-framework') {
                        proj.recommendedFramework = null;
                        Store.updateProject(proj);
                        render(proj);
                    }
                }
                return;
            }

            const toggle = e.target.closest('[data-toggle-bp]');
            if (!toggle) return;
            const key = toggle.dataset.key;
            const detail = toggle.parentElement.querySelector('.bp-item-detail');
            const chevron = toggle.querySelector('.bp-chevron');
            if (!detail) return;

            const isOpen = detail.style.display !== 'none';
            detail.style.display = isOpen ? 'none' : 'block';
            if (chevron) chevron.classList.toggle('open', !isOpen);

            if (isOpen) {
                _expandedSections.delete(key);
            } else {
                _expandedSections.add(key);
            }
        });

        // Seat time editor change handler
        checklist.addEventListener('change', (e) => {
            const sel = e.target.closest('[data-action="change-seat-time"]');
            if (!sel) return;
            const pid = sel.dataset.project;
            const proj = Store.getProject(pid);
            if (!proj) return;
            const parts = sel.value.split('-');
            proj.seatTime = { min: parseInt(parts[0], 10), max: parseInt(parts[1], 10) };
            Store.updateProject(proj);
            // Update the summary text without full re-render
            const summaryEl = sel.closest('.bp-item').querySelector('.bp-summary');
            if (summaryEl) summaryEl.textContent = `${proj.seatTime.min}\u2013${proj.seatTime.max} min`;
        });
    }

    // ── Detail renderers ─────────────────────────────────────────

    function _objectivesSummary(biz, learn) {
        const parts = [];
        if (biz.length > 0) parts.push(`${biz.length} business`);
        if (learn.length > 0) parts.push(`${learn.length} learning`);
        return parts.length > 0 ? parts.join(', ') : 'None yet';
    }

    function _materialsSummary(uploads, urls) {
        const parts = [];
        if (uploads.length > 0) parts.push(`${uploads.length} file${uploads.length > 1 ? 's' : ''}`);
        if (urls.length > 0) parts.push(`${urls.length} URL${urls.length > 1 ? 's' : ''}`);
        return parts.length > 0 ? parts.join(', ') : 'None yet';
    }

    function _renderAudienceDetail(audiences) {
        return audiences.map(a => `
            <div class="bp-detail-card">
                <div class="bp-detail-role">${escHtml(a.role)}</div>
                ${a.responsibilities ? `<div class="bp-detail-meta">${escHtml(a.responsibilities)}</div>` : ''}
                ${a.prerequisites ? `<div class="bp-detail-meta">Prereqs: ${escHtml(a.prerequisites)}</div>` : ''}
            </div>
        `).join('');
    }

    function _renderObjectivesDetail(biz, learn) {
        let html = '';
        if (biz.length > 0) {
            html += '<div class="bp-detail-sublabel">Business</div><ul class="bp-detail-list">' +
                biz.map(o => `<li>${escHtml(o)}</li>`).join('') + '</ul>';
        }
        if (learn.length > 0) {
            html += '<div class="bp-detail-sublabel">Learning</div><ul class="bp-detail-list">' +
                learn.map(o => `<li>${escHtml(o)}</li>`).join('') + '</ul>';
        }
        return html;
    }

    function _renderListDetail(items) {
        return '<ul class="bp-detail-list">' +
            items.map(item => `<li>${escHtml(item)}</li>`).join('') + '</ul>';
    }

    function _renderMaterialsDetail(uploads, urls) {
        let html = '';
        for (const u of uploads) {
            html += `<div class="bp-detail-file">${escHtml(u.name)}</div>`;
        }
        for (const u of urls) {
            html += `<div class="bp-detail-file">${escHtml(u.title || u.url)}</div>`;
        }
        return html;
    }

    function _renderDocsDetail(refs) {
        return refs.map(r => `
            <div class="bp-detail-file">
                ${escHtml(r.title || r.url)}
                ${r.notes ? `<span class="bp-detail-meta">${escHtml(r.notes)}</span>` : ''}
            </div>
        `).join('');
    }

    function _renderSeatTimeEditor(seatTime, projectId) {
        const current = `${seatTime.min}-${seatTime.max}`;
        const options = [
            { value: '15-30', label: '15–30 min' },
            { value: '30-45', label: '30–45 min' },
            { value: '45-75', label: '45–75 min' },
            { value: '75-90', label: '75–90 min' },
            { value: '90-120', label: '90–120 min' },
        ];
        const opts = options.map(o =>
            `<option value="${o.value}" ${o.value === current ? 'selected' : ''}>${o.label}</option>`
        ).join('');
        return `<div class="bp-seat-time-editor">
            <select class="bp-seat-time-select" data-action="change-seat-time" data-project="${projectId}">
                ${opts}
            </select>
            <div class="bp-seat-time-hint">Drives the number and scope of labs generated in Phase 2</div>
        </div>`;
    }

    function _renderSeedsDetail(seeds) {
        return seeds.map(s => `
            <div class="bp-detail-card">
                <div class="bp-detail-role">${escHtml(s.title)}</div>
                ${s.description ? `<div class="bp-detail-meta">${escHtml(s.description)}</div>` : ''}
            </div>
        `).join('');
    }

    function _competenciesSummary(competencies, recFramework) {
        const parts = [];
        if (recFramework) parts.push(recFramework.name);
        if (competencies.length > 0) parts.push(`${competencies.length} skills`);
        return parts.length > 0 ? parts.join(' · ') : 'None yet';
    }

    function _renderCompetenciesDetail(competencies, recFramework, projectId) {
        let html = '';

        // Framework recommendation banner
        if (recFramework) {
            const accepted = recFramework.accepted;
            html += `<div class="bp-framework-rec">`;
            html += `<div class="bp-framework-name">${escHtml(recFramework.name)}</div>`;
            if (recFramework.reason) {
                html += `<div class="bp-framework-reason">${escHtml(recFramework.reason)}</div>`;
            }
            if (recFramework.alternatives && recFramework.alternatives.length > 0) {
                html += `<div class="bp-framework-alts">Alternatives: ${recFramework.alternatives.map(a => escHtml(a)).join(', ')}</div>`;
            }
            if (!accepted) {
                html += `<div class="bp-framework-actions">`;
                html += `<button class="bp-framework-accept" data-action="accept-framework" data-project="${projectId}">Use this framework</button>`;
                html += `<button class="bp-framework-ignore" data-action="ignore-framework" data-project="${projectId}">No framework</button>`;
                html += `</div>`;
            } else {
                html += `<div class="bp-framework-status">✓ Active framework</div>`;
            }
            html += `</div>`;
        }

        // Group competencies by source
        if (competencies.length > 0) {
            const bySource = {};
            for (const c of competencies) {
                const src = c.source || 'Unknown';
                if (!bySource[src]) bySource[src] = [];
                bySource[src].push(c);
            }

            for (const [source, comps] of Object.entries(bySource)) {
                html += `<div class="bp-source-group">`;
                html += `<div class="bp-source-label">${escHtml(source)}</div>`;
                html += '<div class="bp-detail-tags">' +
                    comps.map(c =>
                        `<span class="bp-tag" title="${escHtml(c.description || '')}">${escHtml(c.name)}</span>`
                    ).join('') + '</div>';
                html += '</div>';
            }
        }

        return html;
    }

    // ── Data mutation helpers (still needed for inline edits) ────

    function _removeUpload(projectId, uploadId) {
        const project = Store.getProject(projectId);
        if (!project) return;
        project.uploads = (project.uploads || []).filter(u => u.id !== uploadId);
        Store.updateProject(project);
    }

    function _removeUrl(projectId, urlId) {
        const project = Store.getProject(projectId);
        if (!project) return;
        project.urls = (project.urls || []).filter(u => u.id !== urlId);
        Store.updateProject(project);
    }

    function _removeCompetency(projectId, competencyId) {
        const project = Store.getProject(projectId);
        if (!project) return;
        project.competencies = (project.competencies || []).filter(c => c.id !== competencyId);
        Store.updateProject(project);
    }

    // ── File upload handler ─────────────────────────────────────

    function handleUpload(file, projectId) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            Store.addUpload(projectId, {
                name: file.name,
                type: file.type || 'unknown',
                content: ev.target.result,
            });
            const project = Store.getProject(projectId);
            if (project) render(project);
        };
        reader.onerror = () => {
            console.warn('[Phase1] Failed to read file:', file.name);
        };
        reader.readAsText(file);
    }

    // ── URL add handler ─────────────────────────────────────────

    function handleAddUrl(url, projectId) {
        const title = _extractTitleFromUrl(url);

        fetch(url, { mode: 'cors' })
            .then(resp => {
                if (!resp.ok) throw new Error('Fetch failed');
                return resp.text();
            })
            .then(text => {
                const plainText = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
                const truncated = plainText.length > 50000 ? plainText.substring(0, 50000) + '...' : plainText;

                Store.addUrl(projectId, { url, title, content: truncated });
                const project = Store.getProject(projectId);
                if (project) render(project);
            })
            .catch(() => {
                Store.addUrl(projectId, { url, title, content: '' });
                const project = Store.getProject(projectId);
                if (project) render(project);
            });
    }

    function _extractTitleFromUrl(url) {
        try {
            const u = new URL(url);
            const segments = u.pathname.split('/').filter(Boolean);
            if (segments.length > 0) {
                return decodeURIComponent(segments[segments.length - 1]).replace(/[-_]/g, ' ');
            }
            return u.hostname;
        } catch {
            return url;
        }
    }

    // ── Apply AI results ────────────────────────────────────────

    function applyAIResults(structured, projectId) {
        if (!structured) return;

        const project = Store.getProject(projectId);
        if (!project) return;

        // Program name
        if (structured.programName && structured.programName !== 'Untitled Program') {
            project.name = structured.programName;
            if (typeof window._appSetProgramName === 'function') {
                window._appSetProgramName(structured.programName);
            }
        }

        // Technology/Platform
        if (structured.technologyPlatform) {
            project.technologyPlatform = structured.technologyPlatform;
        }

        // Merge audiences
        if (Array.isArray(structured.audiences)) {
            const existingRoles = new Set((project.audiences || []).map(a => a.role.toLowerCase()));
            for (const a of structured.audiences) {
                const role = a.role || a.name || '';
                if (!role || existingRoles.has(role.toLowerCase())) continue;
                project.audiences.push({
                    id: Store.generateId(),
                    role,
                    responsibilities: a.responsibilities || '',
                    prerequisites: a.prerequisites || '',
                });
                existingRoles.add(role.toLowerCase());
            }
        }

        // Merge business objectives
        if (Array.isArray(structured.businessObjectives)) {
            const existing = new Set((project.businessObjectives || []).map(o => o.toLowerCase()));
            for (const obj of structured.businessObjectives) {
                if (!obj || existing.has(obj.toLowerCase())) continue;
                project.businessObjectives.push(obj);
                existing.add(obj.toLowerCase());
            }
        }

        // Merge learning objectives
        if (Array.isArray(structured.learningObjectives)) {
            const existing = new Set((project.learningObjectives || []).map(o => o.toLowerCase()));
            for (const obj of structured.learningObjectives) {
                if (!obj || existing.has(obj.toLowerCase())) continue;
                project.learningObjectives.push(obj);
                existing.add(obj.toLowerCase());
            }
        }

        // Merge competencies
        if (Array.isArray(structured.competencies)) {
            const existingNames = new Set((project.competencies || []).map(c => c.name.toLowerCase()));
            for (const c of structured.competencies) {
                const name = c.name || c;
                if (!name || existingNames.has(name.toLowerCase())) continue;
                project.competencies.push({
                    id: Store.generateId(),
                    name,
                    description: c.description || '',
                    source: c.source || 'AI-extracted',
                });
                existingNames.add(name.toLowerCase());
            }
        }

        // Merge success criteria
        if (Array.isArray(structured.successCriteria)) {
            if (!Array.isArray(project.successCriteria)) project.successCriteria = [];
            const existing = new Set(project.successCriteria.map(s => s.toLowerCase()));
            for (const sc of structured.successCriteria) {
                if (!sc || existing.has(sc.toLowerCase())) continue;
                project.successCriteria.push(sc);
                existing.add(sc.toLowerCase());
            }
        }

        // Merge documentation refs
        if (Array.isArray(structured.documentationRefs)) {
            if (!Array.isArray(project.documentationRefs)) project.documentationRefs = [];
            const existingUrls = new Set(project.documentationRefs.map(d => d.url));
            for (const ref of structured.documentationRefs) {
                if (!ref.url || existingUrls.has(ref.url)) continue;
                project.documentationRefs.push({
                    id: Store.generateId(),
                    url: ref.url,
                    title: ref.title || ref.url,
                    notes: ref.notes || '',
                });
                existingUrls.add(ref.url);
            }
        }

        // Recommended difficulty
        if (structured.recommendedDifficulty) {
            project.recommendedDifficulty = structured.recommendedDifficulty;
        }

        // Recommended framework
        if (structured.recommendedFramework && !project.recommendedFramework) {
            project.recommendedFramework = {
                name: structured.recommendedFramework.name || structured.recommendedFramework,
                reason: structured.recommendedFramework.reason || '',
                alternatives: structured.recommendedFramework.alternatives || [],
                accepted: false,
            };
        }

        // Merge scenario seeds
        if (Array.isArray(structured.scenarioSeeds)) {
            if (!Array.isArray(project.scenarioSeeds)) project.scenarioSeeds = [];
            const existingTitles = new Set(project.scenarioSeeds.map(s => s.title.toLowerCase()));
            for (const seed of structured.scenarioSeeds) {
                if (!seed.title || existingTitles.has(seed.title.toLowerCase())) continue;
                project.scenarioSeeds.push({
                    id: Store.generateId(),
                    title: seed.title,
                    description: seed.description || '',
                });
                existingTitles.add(seed.title.toLowerCase());
            }
        }

        Store.updateProject(project);
        render(project);
    }

    // ── Context summary for later phases ────────────────────────

    function getContextSummary(projectId) {
        const project = Store.getProject(projectId);
        if (!project) return '';

        const parts = [];

        if (project.technologyPlatform) {
            parts.push('Technology/Platform: ' + project.technologyPlatform);
        }

        const audiences = project.audiences || [];
        if (audiences.length > 0) {
            parts.push('Target Audiences:');
            audiences.forEach(a => {
                let line = `  - ${a.role}`;
                if (a.responsibilities) line += ` (responsibilities: ${a.responsibilities})`;
                if (a.prerequisites) line += ` (prerequisites: ${a.prerequisites})`;
                parts.push(line);
            });
        }

        const bizObj = project.businessObjectives || [];
        if (bizObj.length > 0) {
            parts.push('Business Objectives:');
            bizObj.forEach(o => parts.push(`  - ${o}`));
        }

        const learnObj = project.learningObjectives || [];
        if (learnObj.length > 0) {
            parts.push('Learning Objectives:');
            learnObj.forEach(o => parts.push(`  - ${o}`));
        }

        const criteria = project.successCriteria || [];
        if (criteria.length > 0) {
            parts.push('Success Criteria:');
            criteria.forEach(c => parts.push(`  - ${c}`));
        }

        const competencies = project.competencies || [];
        if (competencies.length > 0) {
            parts.push('Competencies:');
            competencies.forEach(c => {
                let line = `  - ${c.name}`;
                if (c.source) line += ` [${c.source}]`;
                parts.push(line);
            });
        }

        const docRefs = project.documentationRefs || [];
        if (docRefs.length > 0) {
            parts.push('Documentation References:');
            docRefs.forEach(r => parts.push(`  - ${r.title || r.url}`));
        }

        const seeds = project.scenarioSeeds || [];
        if (seeds.length > 0) {
            parts.push('Scenario Seeds:');
            seeds.forEach(s => parts.push(`  - ${s.title}: ${s.description}`));
        }

        const uploads = project.uploads || [];
        const urls = project.urls || [];
        if (uploads.length > 0 || urls.length > 0) {
            parts.push('Source Materials:');
            uploads.forEach(u => parts.push(`  - File: ${u.name}`));
            urls.forEach(u => parts.push(`  - URL: ${u.title || u.url}`));
        }

        return parts.join('\n');
    }

    // ── Public API ──────────────────────────────────────────────

    return {
        init,
        render,
        handleUpload,
        handleAddUrl,
        applyAIResults,
        getContextSummary,
    };
})();
