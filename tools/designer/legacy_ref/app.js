/**
 * app.js — Thin orchestrator for Lab Program Designer v3.
 * Handles navigation, project management, chat dispatch, settings binding,
 * and import/export. Delegates rendering to Phase1-4 controllers.
 *
 * Program selection is handled conversationally in Phase 1 — no sidebar widget.
 */

document.addEventListener('DOMContentLoaded', () => {

    // ── State ──
    let currentProject = null;
    let currentSection = 'phase1';
    let pendingFiles = []; // files waiting to be sent with next message (phase 1)

    // ── DOM helpers ──
    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)];

    // ── Phase number mapping ──
    const PHASE_NUMBERS = { phase1: 1, phase2: 2, phase3: 3, phase4: 4 };

    // ── Phase controllers ──
    const PHASE_CONTROLLERS = {
        1: typeof Phase1 !== 'undefined' ? Phase1 : null,
        2: typeof Phase2 !== 'undefined' ? Phase2 : null,
        3: typeof Phase3 !== 'undefined' ? Phase3 : null,
        4: typeof Phase4 !== 'undefined' ? Phase4 : null,
    };

    // ── Initialize ──
    init();

    function init() {
        // Init all phase controllers
        for (const ctrl of Object.values(PHASE_CONTROLLERS)) {
            if (ctrl && typeof ctrl.init === 'function') ctrl.init();
        }

        Settings.load();

        bindNavigation();
        bindChat('phase1');
        bindChat('phase2');
        bindChat('phase3');
        bindChat('phase4');
        bindFileUpload();
        bindSettings();
        bindProgramName();

        // Load active project (don't auto-create — Phase 1 conversation handles that)
        loadActiveProject();
        renderAll();
        renderChatHistory('phase1');
        showWelcomeIfNeeded();
    }

    // ══════════════════════════════════════════════════════════════
    //  Navigation
    // ══════════════════════════════════════════════════════════════

    function bindNavigation() {
        $$('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                if (section) navigateTo(section);
            });
        });
    }

    function navigateTo(section) {
        currentSection = section;

        // Update nav active states
        $$('.nav-link').forEach(l => l.classList.toggle('active', l.dataset.section === section));

        // Show/hide sections
        $$('.phase-section').forEach(s => s.classList.toggle('active', s.id === `section-${section}`));

        // Render the appropriate phase or settings
        const phaseNum = PHASE_NUMBERS[section];
        if (phaseNum && currentProject) {
            const ctrl = PHASE_CONTROLLERS[phaseNum];
            if (ctrl && typeof ctrl.render === 'function') {
                ctrl.render(currentProject);
            }
            renderChatHistory(section);
            showPhaseWelcomeIfNeeded(section);
        } else if (section === 'settings') {
            renderSettings();
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  Project Management
    // ══════════════════════════════════════════════════════════════

    function loadActiveProject() {
        currentProject = Store.getActiveProject();
        if (!currentProject) {
            // Create a default project — Phase 1 conversation will name it
            currentProject = Store.createProject('Untitled Program');
        }
        updateProgramNameDisplay();
    }

    function updateProgramNameDisplay() {
        // Program name is handled conversationally — no sidebar field
    }

    function bindProgramName() {
        const nameInput = $('#program-name-input');
        if (!nameInput) return;

        const saveName = () => {
            if (!currentProject) return;
            const newName = nameInput.value.trim() || 'Untitled Program';
            nameInput.value = newName;
            currentProject.name = newName;
            Store.updateProject(currentProject);
        };

        nameInput.addEventListener('blur', saveName);
        nameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                nameInput.blur();
            }
        });
    }

    /**
     * Called by Phase 1 AI results when the program is named conversationally.
     */
    function setProgramName(name) {
        if (!currentProject) return;
        currentProject.name = name;
        Store.updateProject(currentProject);
    }

    // Expose for Phase1 to call
    window._appSetProgramName = setProgramName;

    // ══════════════════════════════════════════════════════════════
    //  Chat Handling (shared across phases)
    // ══════════════════════════════════════════════════════════════

    function bindChat(phaseKey) {
        const input = $(`#${phaseKey}-chat-input`);
        const sendBtn = $(`#${phaseKey}-chat-send`);
        if (!input || !sendBtn) return;

        const doSend = () => {
            const text = input.value.trim();
            if (!text && (phaseKey !== 'phase1' || pendingFiles.length === 0)) return;
            sendMessage(phaseKey, text);
            input.value = '';
            input.style.height = 'auto';
        };

        sendBtn.addEventListener('click', doSend);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                doSend();
            }
        });

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });
    }

    async function sendMessage(phaseKey, text) {
        const phaseNum = PHASE_NUMBERS[phaseKey];
        if (!phaseNum) return;

        if (!Settings.isConfigured()) {
            renderChatMessage(phaseKey, 'assistant', 'Please configure your AI provider in Settings first.');
            navigateTo('settings');
            return;
        }

        // Handle file attachments for phase 1
        let messageText = text;
        if (phaseKey === 'phase1' && pendingFiles.length > 0) {
            const fileNames = pendingFiles.map(f => f.name).join(', ');
            messageText = text
                ? `${text}\n\n[Attached files: ${fileNames}]`
                : `I've uploaded these documents: ${fileNames}. Please analyze them.`;

            // Save uploads to project
            pendingFiles.forEach(f => {
                Store.addUpload(currentProject.id, {
                    name: f.name,
                    type: f.type,
                    content: f.content,
                });
            });
            currentProject = Store.getProject(currentProject.id);
            Phase1.render(currentProject);
            pendingFiles = [];
            renderAttachments();
        }

        // Show user message
        renderChatMessage(phaseKey, 'user', messageText);

        // Show typing indicator
        showTypingIndicator(phaseKey);

        try {
            // Refresh project from store
            currentProject = Store.getProject(currentProject.id);

            const result = await Chat.sendMessage(phaseNum, currentProject.id, messageText);

            hideTypingIndicator(phaseKey);

            // Apply structured results to the appropriate phase controller
            if (result.structured) {
                const ctrl = PHASE_CONTROLLERS[phaseNum];
                if (ctrl && typeof ctrl.applyAIResults === 'function') {
                    ctrl.applyAIResults(result.structured, currentProject.id);
                }
            }

            // Refresh project after AI results applied
            currentProject = Store.getProject(currentProject.id);

            // Show cleaned response
            const displayText = result.display;
            if (displayText) {
                renderChatMessage(phaseKey, 'assistant', displayText);
            }

            // Update progress indicators
            updateProgressIndicators();
            updateProgramNameDisplay();
        } catch (err) {
            hideTypingIndicator(phaseKey);
            renderChatMessage(phaseKey, 'assistant', `Error: ${err.message}`);
        }
    }

    function renderChatMessage(phaseKey, role, content) {
        const container = $(`#${phaseKey}-chat-messages`);
        if (!container) return;
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;
        bubble.innerHTML = formatMessage(content);
        container.appendChild(bubble);
        container.scrollTop = container.scrollHeight;
    }

    function renderChatHistory(phaseKey) {
        if (!currentProject) return;
        const container = $(`#${phaseKey}-chat-messages`);
        if (!container) return;
        container.innerHTML = '';
        const history = Store.getChatHistory(currentProject.id, phaseKey);
        history.forEach(msg => renderChatMessage(phaseKey, msg.role, msg.content));
    }

    // ── Skillable-flavored typing phrases ──
    const SKILLABLE_VERBS = {
        phase1: [
            'Skill-scanning your uploads...',
            'Absorbing your learning goals...',
            'Labifying your objectives...',
            'Mapping out the learning journey...',
            'Decoding your audience DNA...',
            'Competency-mining your docs...',
            'Blueprinting the possibilities...',
            'Calibrating the learning path...',
            'Distilling your requirements...',
        ],
        phase2: [
            'Labcrafting your outline...',
            'Structuring the learning adventure...',
            'Forging the activity blueprint...',
            'Architecting your lab series...',
            'Scaffolding the skill journey...',
            'Assembling the lab framework...',
            'Charting the lab landscape...',
            'Skill-weaving your structure...',
            'Sequencing the learning arc...',
        ],
        phase3: [
            'Drafting your guidance...',
            'Instructifying the activities...',
            'Wordsmithing the walkthrough...',
            'Authoring the learning path...',
            'Polishing the lab steps...',
            'Confidence-building the instructions...',
            'Fine-tuning the challenge...',
            'Crafting the discovery moments...',
            'Detailing the skill-builders...',
        ],
        phase4: [
            'Bundling the lab package...',
            'Finalizing the deliverables...',
            'Wiring up the environment...',
            'Scoring the success criteria...',
            'Packaging the experience...',
            'Launch-prepping your labs...',
            'Quality-checking the output...',
            'Export-readying your program...',
        ],
    };

    function _pickSkillableVerb(phaseKey) {
        const verbs = SKILLABLE_VERBS[phaseKey] || SKILLABLE_VERBS.phase1;
        return verbs[Math.floor(Math.random() * verbs.length)];
    }

    function showTypingIndicator(phaseKey) {
        const el = $(`#${phaseKey}-chat-typing`);
        if (!el) return;

        // Update the typing bubble with a Skillable verb
        const verb = _pickSkillableVerb(phaseKey);
        const bubble = el.querySelector('.chat-bubble');
        if (bubble) {
            bubble.innerHTML = `
                <div class="typing-indicator"><span></span><span></span><span></span></div>
                <div class="typing-verb">${verb}</div>
            `;
        }

        el.style.display = 'block';
        const container = $(`#${phaseKey}-chat-messages`);
        if (container) container.scrollTop = container.scrollHeight;
    }

    function hideTypingIndicator(phaseKey) {
        const el = $(`#${phaseKey}-chat-typing`);
        if (el) el.style.display = 'none';
    }

    function formatMessage(text) {
        if (!text) return '';

        // Escape HTML
        let safe = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Split into paragraphs on double-newlines
        const paragraphs = safe.split(/\n\n+/);
        const formatted = paragraphs.map(para => {
            // Apply inline formatting
            let p = para
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/`(.+?)`/g, '<code>$1</code>');

            // Detect if this paragraph is a list (starts with - or numbered)
            const lines = p.split('\n');
            const isList = lines.every(l => l.trim() === '' || /^\s*[-•]\s/.test(l) || /^\s*\d+\.\s/.test(l));

            if (isList && lines.some(l => l.trim() !== '')) {
                const items = lines
                    .filter(l => l.trim() !== '')
                    .map(l => l.replace(/^\s*[-•]\s*/, '').replace(/^\s*\d+\.\s*/, ''))
                    .map(l => `<li>${l}</li>`)
                    .join('');
                return `<ul class="chat-list">${items}</ul>`;
            }

            // Detect if paragraph contains a question (ends with ?)
            const hasQuestion = /\?\s*$/.test(p.trim());
            // Single-line breaks
            p = p.replace(/\n/g, '<br>');

            if (hasQuestion) {
                return `<div class="chat-question">${p}</div>`;
            }
            return `<p>${p}</p>`;
        }).join('');

        return formatted;
    }

    function showWelcomeIfNeeded() {
        if (!currentProject) return;
        const history = Store.getChatHistory(currentProject.id, 'phase1');
        if (history.length === 0) {
            const existingProjects = Store.listProjects();
            const namedProjects = existingProjects.filter(p => p.id !== currentProject.id && p.name !== 'Untitled Program');

            if (namedProjects.length > 0) {
                const programNames = namedProjects.map(p => `- **${p.name}**`).join('\n');
                renderChatMessage('phase1', 'assistant',
                    `Welcome back! You have existing programs:\n${programNames}\n\n` +
                    `Would you like to **continue working on one of these**, or **start a new program**?`
                );
            } else {
                renderChatMessage('phase1', 'assistant',
                    `Tell me about the program you're building.\n\n` +
                    `If you have any documents — like learning objectives, job task analyses, job descriptions, or even a task list — click the paperclip below to upload them and we'll get started.`
                );
            }
        }
    }

    function showPhaseWelcomeIfNeeded(phaseKey) {
        if (!currentProject) return;
        const history = Store.getChatHistory(currentProject.id, phaseKey);
        if (history.length > 0) return; // already has conversation

        if (phaseKey === 'phase2') {
            const hasObjectives = (currentProject.businessObjectives && currentProject.businessObjectives.length > 0) ||
                (currentProject.learningObjectives && currentProject.learningObjectives.length > 0);
            const hasAudiences = currentProject.audiences && currentProject.audiences.length > 0;

            if (!hasObjectives || !hasAudiences) {
                renderChatMessage('phase2', 'assistant',
                    `Looking forward to generating an outline with you, but I need some context first.\n\n` +
                    `If you could answer a few more questions in **Phase 1**, that would help a ton. Or you can upload or paste a starter outline here if you have one.`
                );
            } else {
                renderChatMessage('phase2', 'assistant',
                    `Great — you've got a solid foundation from Phase 1. I'm ready to stub out a suggested lab outline based on your objectives and audiences.\n\n` +
                    `Say **"generate outline"** and I'll create a draft structure with Lab Series, Labs, and Activities. Or paste your own outline here if you already have one.`
                );
            }
        } else if (phaseKey === 'phase3') {
            const hasStructure = currentProject.programStructure &&
                currentProject.programStructure.labSeries &&
                currentProject.programStructure.labSeries.length > 0;

            if (!hasStructure) {
                renderChatMessage('phase3', 'assistant',
                    `Before we draft instructions, we need a lab outline to work from.\n\n` +
                    `Head over to **Phase 2** to generate or define your lab structure first.`
                );
            } else {
                renderChatMessage('phase3', 'assistant',
                    `Your lab outline is ready. Let's start drafting instructions for each activity.\n\n` +
                    `The instruction style defaults to **challenge-based** — you can change it in the Styling tab. Say **"start drafting"** and I'll generate instructions for all your labs.\n\n` +
                    `**Keep in mind:** These are draft instructions — scaffolding to give your lab authors a strong head start. Final editing, polish, and QA will happen in Skillable Studio.`
                );
            }
        } else if (phaseKey === 'phase4') {
            const hasStructure = currentProject.programStructure &&
                currentProject.programStructure.labSeries &&
                currentProject.programStructure.labSeries.length > 0;
            const hasDrafts = currentProject.draftInstructions &&
                Object.keys(currentProject.draftInstructions).length > 0;

            if (!hasStructure) {
                renderChatMessage('phase4', 'assistant',
                    `We're almost there! But I need your lab outline and draft instructions before I can assemble the environment checklist.\n\n` +
                    `Head back to **Phase 2** to build your outline, then **Phase 3** to draft instructions.`
                );
            } else {
                const programName = currentProject.name && currentProject.name !== 'Untitled Program'
                    ? `**${currentProject.name}**` : 'your lab program';
                renderChatMessage('phase4', 'assistant',
                    `Great work! ${programName} is looking like an incredible lab program!\n\n` +
                    `Now that we've thought through everything you want people to do, it's time for me to assemble a checklist of all the **technologies, software, accounts, permissions, tools, configurations, files, and dummy data** you'll need for the environments in these labs.\n\n` +
                    `Before I get started, is there anything special you want to be sure I include?`
                );
            }
        }
    }

    function clearAllChats() {
        ['phase1', 'phase2', 'phase3', 'phase4'].forEach(phaseKey => {
            const container = $(`#${phaseKey}-chat-messages`);
            if (container) container.innerHTML = '';
        });
    }

    function restoreAllChats() {
        ['phase1', 'phase2', 'phase3', 'phase4'].forEach(phaseKey => {
            renderChatHistory(phaseKey);
        });
    }

    // ══════════════════════════════════════════════════════════════
    //  File Upload (Phase 1 paperclip)
    // ══════════════════════════════════════════════════════════════

    function bindFileUpload() {
        const uploadBtn = $('#phase1-upload-btn');
        const fileInput = $('#phase1-file-input');

        if (uploadBtn && fileInput) {
            uploadBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => {
                Array.from(e.target.files).forEach(file => {
                    const reader = new FileReader();
                    reader.onload = (ev) => {
                        pendingFiles.push({
                            name: file.name,
                            type: file.type,
                            size: file.size,
                            content: ev.target.result,
                        });
                        renderAttachments();
                    };
                    reader.readAsText(file);
                });
                e.target.value = '';
            });
        }
    }

    function renderAttachments() {
        const container = $('#phase1-attachments');
        if (!container) return;
        container.innerHTML = pendingFiles.map((f, i) =>
            `<span class="chat-attachment-chip">${escHtml(f.name)} <span class="remove" data-idx="${i}">&times;</span></span>`
        ).join('');
        container.querySelectorAll('.remove').forEach(btn => {
            btn.addEventListener('click', () => {
                pendingFiles.splice(parseInt(btn.dataset.idx), 1);
                renderAttachments();
            });
        });
    }

    // ══════════════════════════════════════════════════════════════
    //  Render All Phases
    // ══════════════════════════════════════════════════════════════

    function renderAll() {
        if (!currentProject) return;

        for (const [num, ctrl] of Object.entries(PHASE_CONTROLLERS)) {
            if (ctrl && typeof ctrl.render === 'function') {
                ctrl.render(currentProject);
            }
        }

        updateProgressIndicators();
    }

    function updateProgressIndicators() {
        if (!currentProject) return;

        // Phase 1: has audiences or objectives
        const p1HasData = (currentProject.audiences && currentProject.audiences.length > 0) ||
            (currentProject.businessObjectives && currentProject.businessObjectives.length > 0) ||
            (currentProject.learningObjectives && currentProject.learningObjectives.length > 0);
        const p1Complete = p1HasData && currentProject.competencies && currentProject.competencies.length > 0;
        setProgressIcon('phase1', p1Complete ? 'check' : (p1HasData ? 'half' : 'empty'));

        // Phase 2: has program structure
        const p2HasData = currentProject.programStructure &&
            currentProject.programStructure.labSeries &&
            currentProject.programStructure.labSeries.length > 0;
        const p2Complete = p2HasData && currentProject.instructionStyle;
        setProgressIcon('phase2', p2Complete ? 'check' : (p2HasData ? 'half' : 'empty'));

        // Phase 3: has lab blueprints with instructions
        const p3HasData = currentProject.labBlueprints && currentProject.labBlueprints.length > 0;
        const p3Complete = p3HasData && currentProject.draftInstructions &&
            Object.keys(currentProject.draftInstructions).length > 0;
        setProgressIcon('phase3', p3Complete ? 'check' : (p3HasData ? 'half' : 'empty'));

        // Phase 4: has environment templates or export
        const p4HasData = (currentProject.environmentTemplates && currentProject.environmentTemplates.length > 0) ||
            (currentProject.scoringMethods && currentProject.scoringMethods.length > 0);
        const p4Complete = p4HasData && currentProject.exportHistory && currentProject.exportHistory.length > 0;
        setProgressIcon('phase4', p4Complete ? 'check' : (p4HasData ? 'half' : 'empty'));
    }

    function setProgressIcon(phaseKey, state) {
        const el = $(`#nav-progress-${phaseKey}`);
        if (!el) return;
        switch (state) {
            case 'check':
                el.innerHTML = '<span class="progress-icon complete">&#10003;</span>';
                el.title = 'Complete';
                break;
            case 'half':
                el.innerHTML = '<span class="progress-icon in-progress">&#9679;</span>';
                el.title = 'In progress — check the Lab Blueprint';
                break;
            default:
                el.innerHTML = '<span class="progress-icon empty">&#9675;</span>';
                el.title = 'Not started';
                break;
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  Settings Panel
    // ══════════════════════════════════════════════════════════════

    function renderSettings() {
        const s = Settings.getAll();

        $('#settings-ai-provider').value = s.aiProvider || 'claude';
        $('#settings-api-key').value = s.apiKey || '';
        const provider = s.aiProvider || 'claude';
        filterModelsByProvider(provider);
        const modelSelect = $('#settings-model');
        if (s.model) modelSelect.value = s.model;
        if (!modelSelect.value) {
            const firstOpt = $(`#settings-model optgroup[data-provider="${provider}"] option`);
            if (firstOpt) modelSelect.value = firstOpt.value;
        }
        $('#settings-endpoint').value = s.customEndpoint || '';
        const validSeatTimes = ['15-30', '30-45', '45-75', '75-90', '90-120', '120+'];
        const seatTime = validSeatTimes.includes(s.defaultSeatTime) ? s.defaultSeatTime : '45-75';
        $('#settings-default-seat-time').value = seatTime;
        const apl = s.activitiesPerLab;
        const validApl = ['1-2', '3-5', '6-10', 'unlimited'];
        $('#settings-activities-per-lab').value = validApl.includes(apl) ? apl : '3-5';
        $('#settings-default-difficulty').value = s.defaultDifficulty || 'intermediate';

        // Naming formula
        const namingInput = $('#settings-naming-formula');
        if (namingInput) namingInput.value = s.labNamingFormula || '{Verb} {Specific Action} {Product Name}';

        // Style guide
        const styleSelect = $('#settings-style-guide');
        if (styleSelect) {
            // If custom guide URL exists, ensure it's in the dropdown
            if (s.customStyleGuideUrl) {
                _ensureCustomStyleOption(s.customStyleGuideUrl);
                styleSelect.value = 'custom';
            } else {
                styleSelect.value = s.instructionStyleGuide || 'microsoft';
            }
        }
        const customUrlInput = $('#settings-custom-style-url');
        if (customUrlInput) customUrlInput.value = s.customStyleGuideUrl || '';

        // Always-on references
        const refUrl1 = $('#settings-ref-url-1');
        const refUrl2 = $('#settings-ref-url-2');
        if (refUrl1) refUrl1.value = s.refUrl1 || '';
        if (refUrl2) refUrl2.value = s.refUrl2 || '';
        // Reference file preview
        const refPreview = $('#settings-ref-file-preview');
        const refDropzone = $('#settings-ref-dropzone');
        if (refPreview && s.refFileName) {
            refPreview.innerHTML = `<span class="ref-file-name">${escHtml(s.refFileName)}</span>`;
            if (refDropzone) refDropzone.classList.add('has-logo');
        } else if (refPreview) {
            refPreview.innerHTML = '';
            if (refDropzone) refDropzone.classList.remove('has-logo');
        }

        // Branding
        const brandUrl = $('#settings-branding-source-url');
        if (brandUrl) brandUrl.value = s.brandingSourceUrl || '';
        // Logo preview
        const logoPreview = $('#settings-logo-preview');
        const dropzone = $('#settings-logo-dropzone');
        if (logoPreview) {
            if (s.logoUrl) {
                logoPreview.innerHTML = `<img src="${escHtml(s.logoUrl)}" alt="Logo preview">`;
                if (dropzone) dropzone.classList.add('has-logo');
            } else {
                logoPreview.innerHTML = '';
                if (dropzone) dropzone.classList.remove('has-logo');
            }
        }

        // Endpoint field visibility
        toggleEndpointField(s.aiProvider);

        // (references are rendered inline via ref URL fields and ref file dropzone)
    }

    function bindSettings() {
        // Provider change
        $('#settings-ai-provider').addEventListener('change', (e) => {
            toggleEndpointField(e.target.value);
            filterModelsByProvider(e.target.value);
        });

        // Custom style guide — auto-add to dropdown on blur
        const customStyleInput = $('#settings-custom-style-url');
        if (customStyleInput) {
            customStyleInput.addEventListener('change', () => {
                const url = customStyleInput.value.trim();
                if (url) {
                    _ensureCustomStyleOption(url);
                    $('#settings-style-guide').value = 'custom';
                }
            });
        }

        // Toggle key visibility
        $('#settings-toggle-key').addEventListener('click', () => {
            const input = $('#settings-api-key');
            const btn = $('#settings-toggle-key');
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = 'Hide';
            } else {
                input.type = 'password';
                btn.textContent = 'Show';
            }
        });

        // Test connection
        $('#settings-test-connection').addEventListener('click', async () => {
            const resultEl = $('#settings-test-result');
            resultEl.textContent = 'Testing...';
            resultEl.style.color = '#6b7280';
            saveSettings();
            const result = await Settings.testConnection();
            resultEl.textContent = result.ok ? 'Connected!' : `Failed: ${result.message}`;
            resultEl.style.color = result.ok ? '#10b981' : '#ef4444';
        });

        // Save button
        $('#settings-save').addEventListener('click', () => {
            saveSettings();
            _flashSaved();
        });

        // Auto-save on any change
        const settingsSection = $('#section-settings');
        if (settingsSection) {
            settingsSection.addEventListener('change', () => {
                saveSettings();
                _flashSaved();
            });
            settingsSection.addEventListener('input', _debounce(() => {
                saveSettings();
                _flashSaved();
            }, 600));
        }

        // Logo upload + drag-drop
        const logoDropzone = $('#settings-logo-dropzone');
        const logoInput = $('#settings-logo-upload');
        function handleLogoFile(file) {
            if (!file || !file.type.startsWith('image/')) return;
            const reader = new FileReader();
            reader.onload = (ev) => {
                Settings.set('logoUrl', ev.target.result);
                const preview = $('#settings-logo-preview');
                preview.innerHTML = `<img src="${escHtml(ev.target.result)}" alt="Logo preview">`;
                if (logoDropzone) logoDropzone.classList.add('has-logo');
                _flashSaved();
            };
            reader.readAsDataURL(file);
        }
        if (logoInput) {
            logoInput.addEventListener('change', (e) => {
                handleLogoFile(e.target.files[0]);
                e.target.value = '';
            });
        }
        if (logoDropzone) {
            logoDropzone.addEventListener('dragover', (e) => { e.preventDefault(); logoDropzone.classList.add('dragover'); });
            logoDropzone.addEventListener('dragleave', () => logoDropzone.classList.remove('dragover'));
            logoDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                logoDropzone.classList.remove('dragover');
                handleLogoFile(e.dataTransfer.files[0]);
            });
        }

        // Reference file dropzone
        const refDropzone = $('#settings-ref-dropzone');
        const refFileInput = $('#settings-ref-file-input');
        function handleRefFile(file) {
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (ev) => {
                Settings.set('refFileName', file.name);
                Settings.set('refFileContent', ev.target.result);
                const preview = $('#settings-ref-file-preview');
                if (preview) preview.innerHTML = `<span class="ref-file-name">${escHtml(file.name)}</span>`;
                if (refDropzone) refDropzone.classList.add('has-logo');
                _flashSaved();
            };
            reader.readAsText(file);
        }
        if (refFileInput) {
            refFileInput.addEventListener('change', (e) => {
                handleRefFile(e.target.files[0]);
                e.target.value = '';
            });
        }
        if (refDropzone) {
            refDropzone.addEventListener('dragover', (e) => { e.preventDefault(); refDropzone.classList.add('dragover'); });
            refDropzone.addEventListener('dragleave', () => refDropzone.classList.remove('dragover'));
            refDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                refDropzone.classList.remove('dragover');
                handleRefFile(e.dataTransfer.files[0]);
            });
        }

        // Settings import/export buttons
        const settingsImportBtn = $('#settings-import-project');
        if (settingsImportBtn) {
            settingsImportBtn.addEventListener('click', () => {
                $('#settings-import-file').click();
            });
        }
        const settingsImportFile = $('#settings-import-file');
        if (settingsImportFile) {
            settingsImportFile.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file) return;
                importProjectFromFile(file);
                e.target.value = '';
            });
        }
        const settingsExportBtn = $('#settings-export-project');
        if (settingsExportBtn) {
            settingsExportBtn.addEventListener('click', () => exportProject());
        }
    }

    function _flashSaved() {
        const btn = $('#settings-save');
        if (!btn) return;
        btn.textContent = 'Saved!';
        btn.style.background = '#10b981';
        setTimeout(() => {
            btn.textContent = 'Save Settings';
            btn.style.background = '';
        }, 1500);
    }

    function _debounce(fn, ms) {
        let timer;
        return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
    }

    function saveSettings() {
        Settings.set('aiProvider', $('#settings-ai-provider').value);
        Settings.set('apiKey', $('#settings-api-key').value);
        Settings.set('model', $('#settings-model').value);
        Settings.set('customEndpoint', $('#settings-endpoint').value);
        Settings.set('defaultSeatTime', $('#settings-default-seat-time').value || '45-75');
        Settings.set('activitiesPerLab', $('#settings-activities-per-lab').value || '3-5');
        Settings.set('defaultDifficulty', $('#settings-default-difficulty').value);

        // Naming formula
        const namingInput = $('#settings-naming-formula');
        if (namingInput) Settings.set('labNamingFormula', namingInput.value);

        // Style guide
        const styleSelect = $('#settings-style-guide');
        if (styleSelect) Settings.set('instructionStyleGuide', styleSelect.value);
        const customUrlInput = $('#settings-custom-style-url');
        if (customUrlInput) Settings.set('customStyleGuideUrl', customUrlInput.value);

        const brandUrl = $('#settings-branding-source-url');
        if (brandUrl) Settings.set('brandingSourceUrl', brandUrl.value);

        // Always-on references
        const refUrl1 = $('#settings-ref-url-1');
        if (refUrl1) Settings.set('refUrl1', refUrl1.value);
        const refUrl2 = $('#settings-ref-url-2');
        if (refUrl2) Settings.set('refUrl2', refUrl2.value);

        Settings.save();
    }

    function toggleEndpointField(provider) {
        const group = $('#settings-endpoint-group');
        if (group) group.style.display = provider === 'custom' ? 'block' : 'none';
    }

    function filterModelsByProvider(provider) {
        const select = $('#settings-model');
        if (!select) return;
        const groups = select.querySelectorAll('optgroup');
        groups.forEach(g => {
            g.style.display = g.dataset.provider === provider ? '' : 'none';
        });
        // If current selection is hidden, pick first visible option
        const selected = select.options[select.selectedIndex];
        if (selected && selected.parentElement.style.display === 'none') {
            const visible = select.querySelector(`optgroup[data-provider="${provider}"] option`);
            if (visible) select.value = visible.value;
        }
    }

    function _ensureCustomStyleOption(url) {
        const select = $('#settings-style-guide');
        if (!select) return;
        let customOpt = select.querySelector('option[value="custom"]');
        if (!customOpt) {
            customOpt = document.createElement('option');
            customOpt.value = 'custom';
            select.insertBefore(customOpt, select.firstChild);
        }
        // Show truncated URL as label
        const label = url.length > 40 ? url.substring(0, 37) + '...' : url;
        customOpt.textContent = `Custom: ${label}`;
    }


    // ══════════════════════════════════════════════════════════════
    //  Import / Export
    // ══════════════════════════════════════════════════════════════

    function exportProject() {
        if (!currentProject) return;
        const json = Store.exportProject(currentProject.id);
        if (json) {
            const blob = new Blob([json], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `${currentProject.name.replace(/\s+/g, '-')}.json`;
            a.click();
            URL.revokeObjectURL(a.href);
        }
    }

    function importProjectFromFile(file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            try {
                currentProject = Store.importProject(ev.target.result);
                clearAllChats();
                restoreAllChats();
                renderAll();
                updateProgramNameDisplay();
            } catch (err) {
                alert('Import failed: ' + err.message);
            }
        };
        reader.readAsText(file);
    }

    // ══════════════════════════════════════════════════════════════
    //  Pane Resizer
    // ══════════════════════════════════════════════════════════════

    function bindPaneResizers() {
        $$('.pane-resizer').forEach(resizer => {
            resizer.addEventListener('mousedown', (e) => {
                e.preventDefault();
                const layout = resizer.closest('.phase-layout');
                if (!layout) return;

                const chatPanel = layout.querySelector('.chat-panel');
                const contextPanel = layout.querySelector('.context-panel');
                if (!chatPanel || !contextPanel) return;

                resizer.classList.add('dragging');
                document.body.style.cursor = 'col-resize';
                document.body.style.userSelect = 'none';

                const layoutRect = layout.getBoundingClientRect();
                const resizerWidth = resizer.offsetWidth;

                const onMouseMove = (ev) => {
                    const offsetX = ev.clientX - layoutRect.left;
                    const totalWidth = layoutRect.width - resizerWidth;
                    // Context panel can take at most 50% of available space
                    const minChat = totalWidth * 0.5;
                    const minContext = 280;

                    let chatWidth = Math.max(minChat, Math.min(offsetX, totalWidth - minContext));
                    let contextWidth = totalWidth - chatWidth;

                    chatPanel.style.flex = 'none';
                    chatPanel.style.width = chatWidth + 'px';
                    contextPanel.style.flex = 'none';
                    contextPanel.style.width = contextWidth + 'px';
                    contextPanel.style.minWidth = '0';
                    contextPanel.style.maxWidth = 'none';
                };

                const onMouseUp = () => {
                    resizer.classList.remove('dragging');
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                };

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
        });
    }

    // Initialize resizers
    bindPaneResizers();

    // Expose a small API for phase controllers
    window.App = {
        getCurrentProjectId: () => currentProject ? currentProject.id : null,
        renderChatHistory,
        showWelcomeIfNeeded,
        refreshCurrentProject: () => {
            currentProject = Store.getActiveProject();
            return currentProject;
        },
    };

    // ══════════════════════════════════════════════════════════════
    //  Utilities
    // ══════════════════════════════════════════════════════════════

    function escHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
