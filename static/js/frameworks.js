/**
 * frameworks.js — Skill framework catalog for Lab Program Designer.
 * Contains metadata for public frameworks that can be used for curriculum mapping.
 */

const Frameworks = (() => {
    const catalog = [
        // Cybersecurity
        { id: 'nice', name: 'NICE Workforce Framework', abbrev: 'NICE', publisher: 'NIST', domain: 'Cybersecurity', description: 'Work roles, tasks, knowledge and skills for cybersecurity workforce (SP 800-181r1).' },
        { id: 'dcwf', name: 'DoD Cyber Workforce Framework', abbrev: 'DCWF', publisher: 'U.S. Department of Defense', domain: 'Cybersecurity', description: 'Extension of NICE with DoD-specific cyber work roles and qualifications.' },
        { id: 'mitre-attack', name: 'MITRE ATT&CK', abbrev: 'ATT&CK', publisher: 'MITRE Corporation', domain: 'Cybersecurity', description: 'Knowledge base of adversary tactics and techniques across Enterprise, Mobile, and ICS.' },
        { id: 'comptia-security', name: 'CompTIA Security+ / CySA+ / CASP+', abbrev: 'CompTIA Sec', publisher: 'CompTIA', domain: 'Cybersecurity', description: 'Vendor-neutral cybersecurity certification exam objectives and competency domains.' },

        // Cloud, DevOps & SRE
        { id: 'comptia-cloud', name: 'CompTIA Cloud+', abbrev: 'Cloud+', publisher: 'CompTIA', domain: 'Cloud, DevOps & SRE', description: 'Vendor-neutral cloud computing competency domains covering architecture, security, deployment, and operations.' },
        { id: 'azure-certs', name: 'Microsoft Azure Certifications', abbrev: 'Azure Certs', publisher: 'Microsoft', domain: 'Cloud, DevOps & SRE', description: 'Role-based certifications (Fundamentals, Associate, Expert, Specialty) with structured exam objective domains. Cert-based framework.' },
        { id: 'aws-certs', name: 'AWS Certification Framework', abbrev: 'AWS Certs', publisher: 'Amazon Web Services', domain: 'Cloud, DevOps & SRE', description: 'Role-based certification paths: Practitioner, Associate, Professional, Specialty with detailed skill domains.' },
        { id: 'dasa', name: 'DASA DevOps Competence Model', abbrev: 'DASA', publisher: 'DevOps Agile Skills Association', domain: 'Cloud, DevOps & SRE', description: '4 skill areas and 8 knowledge areas covering technical and behavioral DevOps competencies.' },

        // Data, AI & ML
        { id: 'edison', name: 'EDISON Data Science Framework', abbrev: 'EDSF', publisher: 'EDISON Project (EU)', domain: 'Data & AI', description: 'Competence Framework for Data Science covering analytics, engineering, management, and scientific methods.' },
        { id: 'unesco-ai', name: 'UNESCO AI Competency Framework', abbrev: 'UNESCO AI-CF', publisher: 'UNESCO', domain: 'Data & AI', description: '12 competencies across human-centered mindset, ethics, techniques, and system design.' },
        { id: 'oecd-ai', name: 'OECD AI Literacy Framework', abbrev: 'OECD AI Lit', publisher: 'OECD / European Commission', domain: 'Data & AI', description: 'Four core domains: Engage, Create, Manage, and Design with AI.' },

        // Software Engineering
        { id: 'swebok', name: 'SWEBOK v4', abbrev: 'SWEBOK', publisher: 'IEEE Computer Society', domain: 'Software Engineering', description: '18 Knowledge Areas covering the full scope of software engineering, including architecture, security, and operations.' },
        { id: 'swecom', name: 'SWECOM - SE Competency Model', abbrev: 'SWECOM', publisher: 'IEEE Computer Society', domain: 'Software Engineering', description: 'Competency levels mapped to SWEBOK knowledge areas for software engineering workforce development.' },

        // IT Operations
        { id: 'comptia-infra', name: 'CompTIA A+ / Server+ / Linux+', abbrev: 'CompTIA Ops', publisher: 'CompTIA', domain: 'IT Operations', description: 'Vendor-neutral exam objectives for IT operations, hardware, OS administration, and server infrastructure.' },
        { id: 'itil', name: 'ITIL 4', abbrev: 'ITIL', publisher: 'PeopleCert / Axelos', domain: 'IT Operations', description: 'Service management practices covering incident management, change enablement, monitoring, and capacity management.' },

        // Networking
        { id: 'comptia-network', name: 'CompTIA Network+', abbrev: 'Network+', publisher: 'CompTIA', domain: 'Networking', description: 'Vendor-neutral networking competency domains: fundamentals, implementation, operations, security, troubleshooting.' },
        { id: 'cisco-certs', name: 'Cisco Certification Framework (CCNA / CCNP / CCIE)', abbrev: 'Cisco Certs', publisher: 'Cisco Systems', domain: 'Networking', description: 'Multi-track certification skill domains across Enterprise, Security, Data Center, Service Provider, Collaboration, and DevNet. Covers routing, switching, wireless, automation, and programmability at Associate through Expert levels.' },

        // Project Management
        { id: 'gapps', name: 'GAPPS Project Management Standards', abbrev: 'GAPPS', publisher: 'GAPPS (nonprofit)', domain: 'Project Management', description: 'Open-source, performance-based competency standards for project and program managers.' },
        { id: 'ipma-icb', name: 'IPMA ICB4', abbrev: 'ICB4', publisher: 'IPMA', domain: 'Project Management', description: '42 competencies across Technical, Behavioral, and Contextual areas with Agile reference guide.' },

        // Cross-Domain
        { id: 'sfia', name: 'SFIA 9 - Skills Framework for the Information Age', abbrev: 'SFIA', publisher: 'SFIA Foundation', domain: 'Cross-Domain', description: 'Global framework covering 121 professional skills across all digital/IT disciplines, 7 responsibility levels.' },
        { id: 'ecf', name: 'European e-Competence Framework', abbrev: 'e-CF 4.0', publisher: 'CEN', domain: 'Cross-Domain', description: '41 ICT competences across Plan, Build, Run, Enable, Manage areas mapped to European Qualifications Framework.' },
        { id: 'onet', name: 'O*NET Occupational Framework', abbrev: 'O*NET', publisher: 'U.S. Department of Labor', domain: 'Cross-Domain', description: '923 occupations with structured skills, knowledge, abilities, and task data. Updated quarterly.' },
    ];

    // Custom/uploaded frameworks stored separately
    const customCatalog = [];

    // Combined view: custom frameworks FIRST, then built-in
    function _combined() {
        return [...customCatalog, ...catalog];
    }

    // Group by domain — custom frameworks appear in their own group first
    function getDomains() {
        const domains = {};
        const combined = _combined();

        // Custom frameworks first
        const customs = combined.filter(fw => fw.custom);
        if (customs.length > 0) {
            domains['Your Frameworks'] = customs;
        }

        // Then built-in, preserving catalog order
        combined.filter(fw => !fw.custom).forEach(fw => {
            if (!domains[fw.domain]) domains[fw.domain] = [];
            domains[fw.domain].push(fw);
        });

        return domains;
    }

    function getById(id) {
        return _combined().find(fw => fw.id === id) || null;
    }

    function getAll() {
        return _combined();
    }

    function search(query) {
        const q = query.toLowerCase();
        return _combined().filter(fw =>
            fw.name.toLowerCase().includes(q) ||
            (fw.abbrev && fw.abbrev.toLowerCase().includes(q)) ||
            fw.domain.toLowerCase().includes(q) ||
            fw.description.toLowerCase().includes(q)
        );
    }

    /**
     * registerCustom — Adds a custom framework at runtime.
     * @param {Object} frameworkObj - { id, name, organization, domain, description, competencies: [] }
     * @returns {Object} the registered framework object
     */
    function registerCustom(frameworkObj) {
        const required = ['id', 'name', 'organization', 'domain', 'description'];
        for (const field of required) {
            if (!frameworkObj[field]) {
                throw new Error(`registerCustom: missing required field "${field}"`);
            }
        }
        if (getById(frameworkObj.id)) {
            throw new Error(`registerCustom: framework with id "${frameworkObj.id}" already exists`);
        }
        const fw = {
            id: frameworkObj.id,
            name: frameworkObj.name,
            abbrev: frameworkObj.abbrev || frameworkObj.name,
            publisher: frameworkObj.organization,
            domain: frameworkObj.domain,
            description: frameworkObj.description,
            competencies: Array.isArray(frameworkObj.competencies) ? frameworkObj.competencies : [],
            custom: true
        };
        customCatalog.push(fw);
        return fw;
    }

    /**
     * toPromptContext — Returns a text summary suitable for AI prompt injection.
     * @param {string} [frameworkId] - If provided, summarize one framework; otherwise summarize all.
     * @returns {string}
     */
    function toPromptContext(frameworkId) {
        if (frameworkId) {
            const fw = getById(frameworkId);
            if (!fw) return `Framework "${frameworkId}" not found.`;
            return _formatPromptBlock(fw);
        }
        // Summarize all frameworks grouped by domain
        const domains = getDomains();
        const lines = ['# Available Skill Frameworks', ''];
        for (const [domain, frameworks] of Object.entries(domains)) {
            lines.push(`## ${domain}`);
            frameworks.forEach(fw => {
                lines.push(_formatPromptBlock(fw));
                lines.push('');
            });
        }
        return lines.join('\n');
    }

    function _formatPromptBlock(fw) {
        const parts = [
            `**${fw.name}**`,
            `Organization: ${fw.publisher}`,
            `Domain: ${fw.domain}`,
            `Description: ${fw.description}`
        ];
        if (fw.competencies && fw.competencies.length > 0) {
            parts.push('Competency Areas: ' + fw.competencies.join(', '));
        }
        return parts.join('\n');
    }

    /**
     * parseUploadedFramework — Parses an uploaded framework file into standard format.
     * @param {string} content - Raw file content
     * @param {string} fileType - 'json', 'csv', or 'text'
     * @returns {Object} { name, competencies: [] } (partial framework object)
     */
    function parseUploadedFramework(content, fileType) {
        const type = (fileType || '').toLowerCase().replace('.', '');

        if (type === 'json') {
            const parsed = JSON.parse(content);
            return {
                name: parsed.name || 'Untitled Framework',
                competencies: Array.isArray(parsed.competencies) ? parsed.competencies : []
            };
        }

        if (type === 'csv') {
            const lines = content.trim().split(/\r?\n/);
            if (lines.length === 0) return { name: 'Untitled Framework', competencies: [] };
            // First row is header with competency names
            const header = lines[0].split(',').map(s => s.trim()).filter(Boolean);
            return {
                name: 'Uploaded CSV Framework',
                competencies: header
            };
        }

        // Plain text: extract lines as competency/skill names
        if (type === 'text' || type === 'txt' || !type) {
            const lines = content.trim().split(/\r?\n/)
                .map(line => line.replace(/^[-*•\d.)\s]+/, '').trim())
                .filter(line => line.length > 0 && line.length < 200);
            return {
                name: 'Uploaded Text Framework',
                competencies: lines
            };
        }

        throw new Error(`parseUploadedFramework: unsupported file type "${fileType}"`);
    }

    /**
     * listCustom — Returns only the custom/uploaded frameworks.
     * @returns {Array}
     */
    function listCustom() {
        return [...customCatalog];
    }

    /**
     * removeCustom — Removes a custom framework by ID.
     * @param {string} frameworkId
     * @returns {boolean} true if removed, false if not found
     */
    function removeCustom(frameworkId) {
        const idx = customCatalog.findIndex(fw => fw.id === frameworkId);
        if (idx === -1) return false;
        customCatalog.splice(idx, 1);
        return true;
    }

    return {
        getDomains, getById, getAll, search,
        registerCustom, toPromptContext, parseUploadedFramework,
        listCustom, removeCustom
    };
})();
