/**
 * catalog.js — Built-in knowledge base for the Lab Program Designer wizard.
 * Contains skill catalogs, keyword mappings, lab templates, environment presets, and scoring methods.
 */

const Catalog = (() => {

    // ---- Skill Domains ----
    const domains = [
        {
            id: 'compute', name: 'Compute',
            skills: [
                { name: 'Virtual Machines', keywords: ['vm', 'virtual machine', 'compute', 'server', 'instance', 'ec2', 'deploy'] },
                { name: 'App Services', keywords: ['app service', 'web app', 'paas', 'hosting'] },
                { name: 'Serverless Functions', keywords: ['function', 'serverless', 'lambda', 'cloud function', 'automation'] },
                { name: 'Containers', keywords: ['container', 'docker', 'aci', 'ecs', 'cloud run'] },
                { name: 'Kubernetes', keywords: ['kubernetes', 'k8s', 'aks', 'eks', 'gke', 'orchestration'] },
                { name: 'Scale Sets & Auto Scaling', keywords: ['scale', 'auto scale', 'vmss', 'scaling', 'elasticity'] },
            ],
        },
        {
            id: 'networking', name: 'Networking',
            skills: [
                { name: 'Virtual Networks', keywords: ['vnet', 'vpc', 'virtual network', 'subnet', 'network'] },
                { name: 'Load Balancing', keywords: ['load balancer', 'lb', 'traffic', 'application gateway', 'alb'] },
                { name: 'DNS & Domain Management', keywords: ['dns', 'domain', 'zone', 'route 53', 'cloud dns'] },
                { name: 'VPN & Connectivity', keywords: ['vpn', 'expressroute', 'direct connect', 'peering', 'hybrid'] },
                { name: 'CDN & Caching', keywords: ['cdn', 'caching', 'front door', 'cloudfront'] },
            ],
        },
        {
            id: 'security', name: 'Security',
            skills: [
                { name: 'Network Security Groups', keywords: ['nsg', 'firewall', 'security group', 'acl', 'secure', 'security'] },
                { name: 'Identity & Access Management', keywords: ['iam', 'rbac', 'identity', 'access', 'role', 'permission', 'entra', 'active directory', 'ad'] },
                { name: 'Key Vault & Secrets', keywords: ['key vault', 'secrets', 'certificate', 'encryption key', 'kms', 'secret manager'] },
                { name: 'Security Center & Compliance', keywords: ['defender', 'security center', 'compliance', 'policy', 'governance', 'sentinel', 'guard duty'] },
                { name: 'Encryption & Data Protection', keywords: ['encrypt', 'tls', 'ssl', 'data protection', 'disk encryption'] },
            ],
        },
        {
            id: 'storage', name: 'Storage',
            skills: [
                { name: 'Blob & Object Storage', keywords: ['blob', 'storage account', 's3', 'object storage', 'bucket', 'cloud storage'] },
                { name: 'File Storage', keywords: ['file share', 'azure files', 'efs', 'filestore', 'nfs'] },
                { name: 'Disk Management', keywords: ['disk', 'managed disk', 'ebs', 'persistent disk', 'volume'] },
            ],
        },
        {
            id: 'identity', name: 'Identity',
            skills: [
                { name: 'User & Group Management', keywords: ['user', 'group', 'account', 'directory', 'tenant'] },
                { name: 'Multi-Factor Authentication', keywords: ['mfa', 'multi-factor', '2fa', 'authentication', 'conditional access'] },
                { name: 'Single Sign-On', keywords: ['sso', 'single sign-on', 'federation', 'saml', 'oidc'] },
            ],
        },
        {
            id: 'databases', name: 'Databases',
            skills: [
                { name: 'Relational Databases', keywords: ['sql', 'database', 'rds', 'mysql', 'postgres', 'sql server', 'cloud sql'] },
                { name: 'NoSQL Databases', keywords: ['nosql', 'cosmos', 'dynamodb', 'firestore', 'mongodb', 'table storage'] },
                { name: 'Database Migration', keywords: ['migration', 'migrate', 'data migration', 'dms'] },
            ],
        },
        {
            id: 'devops', name: 'DevOps & CI/CD',
            skills: [
                { name: 'CI/CD Pipelines', keywords: ['ci/cd', 'pipeline', 'devops', 'build', 'release', 'github actions', 'codepipeline'] },
                { name: 'Infrastructure as Code', keywords: ['iac', 'terraform', 'arm template', 'bicep', 'cloudformation', 'infrastructure as code'] },
                { name: 'Source Control', keywords: ['git', 'repo', 'source control', 'version control', 'codecommit'] },
                { name: 'Configuration Management', keywords: ['ansible', 'puppet', 'chef', 'dsc', 'configuration'] },
            ],
        },
        {
            id: 'monitoring', name: 'Monitoring & Logging',
            skills: [
                { name: 'Monitoring & Alerts', keywords: ['monitor', 'alert', 'metric', 'cloudwatch', 'application insights', 'observability'] },
                { name: 'Log Analytics', keywords: ['log', 'log analytics', 'logging', 'cloudtrail', 'audit', 'diagnostic'] },
                { name: 'Cost Management', keywords: ['cost', 'billing', 'budget', 'cost management', 'pricing'] },
            ],
        },
        {
            id: 'governance', name: 'Governance & Compliance',
            skills: [
                { name: 'Resource Organization', keywords: ['resource group', 'tag', 'tagging', 'organization', 'management group', 'ou'] },
                { name: 'Policy & Blueprints', keywords: ['policy', 'blueprint', 'guardrail', 'scp', 'org policy', 'governance'] },
                { name: 'Backup & Recovery', keywords: ['backup', 'recovery', 'disaster recovery', 'dr', 'site recovery', 'replication'] },
            ],
        },
    ];

    // ---- Platform detection ----
    function detectPlatform(text) {
        const t = text.toLowerCase();
        const azure = /azure|microsoft cloud|entra|arm template|bicep/.test(t);
        const aws = /\baws\b|amazon web services|ec2|s3 bucket|cloudformation/.test(t);
        const gcp = /\bgcp\b|google cloud|cloud run|bigquery|cloud sql/.test(t);
        const count = [azure, aws, gcp].filter(Boolean).length;
        if (count > 1) return 'multi';
        if (azure) return 'azure';
        if (aws) return 'aws';
        if (gcp) return 'gcp';
        return 'azure'; // default
    }

    // ---- Keyword matching ----
    function matchSkills(text) {
        const lower = text.toLowerCase();
        const matched = [];

        // Check for broad terms that should include foundational skills
        const isBroad = /deploy|admin|fundamentals|basics|introduction|getting started|manage|operate/.test(lower);

        domains.forEach(domain => {
            domain.skills.forEach(skill => {
                const hit = skill.keywords.some(kw => lower.includes(kw));
                if (hit) {
                    matched.push({ domain: domain.id, domainName: domain.name, skill: skill.name });
                }
            });
        });

        // If broad program description, add foundational skills
        if (isBroad && matched.length < 6) {
            const foundational = [
                { domain: 'compute', domainName: 'Compute', skill: 'Virtual Machines' },
                { domain: 'networking', domainName: 'Networking', skill: 'Virtual Networks' },
                { domain: 'security', domainName: 'Security', skill: 'Network Security Groups' },
                { domain: 'security', domainName: 'Security', skill: 'Identity & Access Management' },
                { domain: 'storage', domainName: 'Storage', skill: 'Blob & Object Storage' },
                { domain: 'governance', domainName: 'Governance & Compliance', skill: 'Resource Organization' },
                { domain: 'monitoring', domainName: 'Monitoring & Logging', skill: 'Monitoring & Alerts' },
            ];
            foundational.forEach(f => {
                if (!matched.find(m => m.skill === f.skill)) matched.push(f);
            });
        }

        return matched;
    }

    // ---- Environment presets ----
    const envPresets = {
        azure: {
            platform: 'azure',
            credentials: 'Username: LabUser\nPassword: Provided at lab launch\nSubscription: Lab-Sub-01\nResource Group: lab-rg-01',
            baseVMs: [
                { name: 'LabVM-Win', os: 'windows-11' },
            ],
        },
        aws: {
            platform: 'aws',
            credentials: 'IAM User: lab-user\nConsole URL: Provided at lab launch\nRegion: us-east-1',
            baseVMs: [],
        },
        gcp: {
            platform: 'gcp',
            credentials: 'Project: lab-project-01\nService Account: Provided at lab launch\nRegion: us-central1',
            baseVMs: [],
        },
        multi: {
            platform: 'multi',
            credentials: 'Cloud credentials provided at lab launch for each platform.',
            baseVMs: [],
        },
    };

    // ---- Scoring methods ----
    const scoringMethods = {
        'resource-validation': { name: 'Resource Validation', description: 'Automated check verifies the expected cloud resources exist and are correctly configured.' },
        'task-completion': { name: 'Task Completion', description: 'Learner marks each task as complete; instructor verifies during or after the lab.' },
        'script-check': { name: 'Automated Script Check', description: 'A PowerShell or Bash script runs at the end of the lab to validate outcomes.' },
        'screenshot': { name: 'Screenshot Verification', description: 'Learner submits screenshots of completed tasks for manual review.' },
        'quiz': { name: 'Knowledge Check Quiz', description: 'Short quiz at the end of the lab tests comprehension of key concepts.' },
    };

    // ---- Lab Templates ----
    // Each template maps to a skill and provides a lab outline structure.
    const labTemplates = {
        'Virtual Machines': [
            {
                title: 'Deploy and Configure a Virtual Machine',
                description: 'Provision a virtual machine, configure its size and networking, connect via remote desktop or SSH, and verify connectivity.',
                duration: 45,
                difficulty: 'beginner',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'Virtual Machine', name: 'lab-vm-01' }, { type: 'Public IP', name: 'lab-vm-01-pip' }],
                envVMs: [{ name: 'LabVM-01', os: 'windows-server' }],
                envNotes: 'VM is pre-provisioned with a public IP. Learner configures additional settings.',
                tasks: [
                    {
                        name: 'Create the Virtual Machine',
                        activities: [
                            { title: 'Navigate to the VM creation wizard', instructions: 'Open the cloud portal and navigate to the Virtual Machines service. Click "+ Create" to begin.' },
                            { title: 'Configure VM settings', instructions: 'Set the VM name, region, size (Standard B2s or equivalent), and OS image. Configure administrator credentials.' },
                            { title: 'Review and create', instructions: 'Review all settings on the summary page. Click "Create" and wait for deployment to complete.' },
                        ],
                    },
                    {
                        name: 'Connect to the Virtual Machine',
                        activities: [
                            { title: 'Obtain connection details', instructions: 'Navigate to the VM overview page and note the public IP address.' },
                            { title: 'Connect using RDP or SSH', instructions: 'Use Remote Desktop (Windows) or SSH (Linux) to connect to the VM using the credentials you configured.' },
                            { title: 'Verify the connection', instructions: 'Confirm you are logged in and can access the desktop or command line.' },
                        ],
                    },
                    {
                        name: 'Configure VM Settings',
                        activities: [
                            { title: 'Resize the VM', instructions: 'In the portal, change the VM size to a different SKU and observe the restart process.' },
                            { title: 'Add a data disk', instructions: 'Attach a new managed data disk to the VM. Initialize and format it from within the OS.' },
                        ],
                    },
                ],
            },
        ],
        'App Services': [
            {
                title: 'Deploy a Web Application to App Service',
                description: 'Create an App Service plan, deploy a sample web application, configure custom domains and scaling rules.',
                duration: 40,
                difficulty: 'beginner',
                scoring: ['resource-validation', 'script-check'],
                envResources: [{ type: 'App Service Plan', name: 'lab-asp-01' }, { type: 'Web App', name: 'lab-webapp-01' }],
                envVMs: [],
                envNotes: 'App Service Plan is pre-created. Learner deploys code.',
                tasks: [
                    {
                        name: 'Create the Web App',
                        activities: [
                            { title: 'Create an App Service', instructions: 'Navigate to App Services and create a new web app. Select the runtime stack and region.' },
                            { title: 'Deploy sample code', instructions: 'Use the deployment center or CLI to deploy the provided sample application.' },
                        ],
                    },
                    {
                        name: 'Configure and Scale',
                        activities: [
                            { title: 'Configure application settings', instructions: 'Add environment variables and connection strings in the Configuration blade.' },
                            { title: 'Enable auto-scaling', instructions: 'Configure scale-out rules based on CPU usage thresholds.' },
                        ],
                    },
                ],
            },
        ],
        'Serverless Functions': [
            {
                title: 'Build and Deploy a Serverless Function',
                description: 'Create a serverless function triggered by HTTP requests, configure bindings, and test the function.',
                duration: 35,
                difficulty: 'intermediate',
                scoring: ['script-check', 'task-completion'],
                envResources: [{ type: 'Function App', name: 'lab-func-01' }, { type: 'Storage Account', name: 'labfuncstor01' }],
                envVMs: [],
                envNotes: 'Storage account is pre-provisioned for function state.',
                tasks: [
                    {
                        name: 'Create the Function App',
                        activities: [
                            { title: 'Provision the Function App', instructions: 'Create a new Function App with the appropriate runtime and hosting plan.' },
                            { title: 'Create an HTTP-triggered function', instructions: 'Add a new function using the HTTP trigger template. Test it with a browser request.' },
                        ],
                    },
                    {
                        name: 'Add Bindings and Test',
                        activities: [
                            { title: 'Configure input/output bindings', instructions: 'Add a storage queue output binding to the function.' },
                            { title: 'Test end-to-end', instructions: 'Send HTTP requests and verify messages appear in the queue.' },
                        ],
                    },
                ],
            },
        ],
        'Containers': [
            {
                title: 'Deploy a Containerized Application',
                description: 'Build a Docker container image, push it to a container registry, and deploy it to a container service.',
                duration: 50,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'script-check'],
                envResources: [{ type: 'Container Registry', name: 'labacr01' }, { type: 'Container Instance', name: 'lab-aci-01' }],
                envVMs: [{ name: 'DevVM', os: 'ubuntu' }],
                envNotes: 'DevVM has Docker pre-installed. Registry is pre-created.',
                tasks: [
                    {
                        name: 'Build the Container Image',
                        activities: [
                            { title: 'Review the Dockerfile', instructions: 'Examine the provided Dockerfile and understand its layers.' },
                            { title: 'Build and tag the image', instructions: 'Run docker build to create the image and tag it for the registry.' },
                            { title: 'Push to the registry', instructions: 'Authenticate to the container registry and push the image.' },
                        ],
                    },
                    {
                        name: 'Deploy the Container',
                        activities: [
                            { title: 'Create a container instance', instructions: 'Deploy the image from the registry to a container instance with port 80 exposed.' },
                            { title: 'Verify the deployment', instructions: 'Access the public IP of the container and confirm the application is running.' },
                        ],
                    },
                ],
            },
        ],
        'Kubernetes': [
            {
                title: 'Deploy and Manage a Kubernetes Cluster',
                description: 'Provision a managed Kubernetes cluster, deploy workloads using kubectl, and configure services and scaling.',
                duration: 60,
                difficulty: 'advanced',
                scoring: ['script-check', 'resource-validation'],
                envResources: [{ type: 'Kubernetes Cluster', name: 'lab-k8s-01' }, { type: 'Container Registry', name: 'labacr01' }],
                envVMs: [{ name: 'DevVM', os: 'ubuntu' }],
                envNotes: 'Cluster is pre-provisioned. kubectl is configured on DevVM.',
                tasks: [
                    {
                        name: 'Explore the Cluster',
                        activities: [
                            { title: 'Connect to the cluster', instructions: 'Use the CLI to get cluster credentials and verify connectivity with kubectl get nodes.' },
                            { title: 'Explore namespaces and pods', instructions: 'List all namespaces and pods running in the cluster.' },
                        ],
                    },
                    {
                        name: 'Deploy a Workload',
                        activities: [
                            { title: 'Create a deployment', instructions: 'Apply the provided YAML manifest to create a deployment with 2 replicas.' },
                            { title: 'Expose with a service', instructions: 'Create a LoadBalancer service to expose the deployment externally.' },
                            { title: 'Scale the deployment', instructions: 'Scale the deployment to 4 replicas and observe the pod distribution.' },
                        ],
                    },
                ],
            },
        ],
        'Scale Sets & Auto Scaling': [
            {
                title: 'Configure Auto Scaling for Compute Resources',
                description: 'Set up auto-scaling rules for virtual machine scale sets or instance groups based on performance metrics.',
                duration: 40,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'VM Scale Set', name: 'lab-vmss-01' }, { type: 'Load Balancer', name: 'lab-lb-01' }],
                envVMs: [],
                envNotes: 'Scale set is pre-created with a base image.',
                tasks: [
                    {
                        name: 'Configure Scaling Rules',
                        activities: [
                            { title: 'Define scale-out rules', instructions: 'Create a rule to add instances when average CPU exceeds 70%.' },
                            { title: 'Define scale-in rules', instructions: 'Create a rule to remove instances when average CPU drops below 30%.' },
                        ],
                    },
                    {
                        name: 'Test Scaling',
                        activities: [
                            { title: 'Generate load', instructions: 'SSH into an instance and run a stress test to trigger scale-out.' },
                            { title: 'Verify scaling events', instructions: 'Monitor the activity log to confirm new instances were added.' },
                        ],
                    },
                ],
            },
        ],
        'Virtual Networks': [
            {
                title: 'Configure Virtual Networking',
                description: 'Create virtual networks with subnets, configure peering, and verify connectivity between resources.',
                duration: 40,
                difficulty: 'beginner',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'Virtual Network', name: 'lab-vnet-01' }, { type: 'Virtual Network', name: 'lab-vnet-02' }],
                envVMs: [{ name: 'VM-Subnet-A', os: 'windows-server' }, { name: 'VM-Subnet-B', os: 'ubuntu' }],
                envNotes: 'Two VNets are pre-created. VMs are deployed into each.',
                tasks: [
                    {
                        name: 'Create Subnets and Assign Resources',
                        activities: [
                            { title: 'Add subnets', instructions: 'Create additional subnets in each virtual network with appropriate CIDR ranges.' },
                            { title: 'Verify IP assignments', instructions: 'Check that each VM has received an IP from its assigned subnet.' },
                        ],
                    },
                    {
                        name: 'Configure Network Peering',
                        activities: [
                            { title: 'Create a peering connection', instructions: 'Establish bidirectional peering between the two virtual networks.' },
                            { title: 'Test connectivity', instructions: 'Ping from VM-Subnet-A to VM-Subnet-B to verify the peering works.' },
                        ],
                    },
                ],
            },
        ],
        'Load Balancing': [
            {
                title: 'Implement Load Balancing',
                description: 'Deploy a load balancer, configure backend pools and health probes, and test traffic distribution.',
                duration: 35,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'script-check'],
                envResources: [{ type: 'Load Balancer', name: 'lab-lb-01' }, { type: 'Public IP', name: 'lab-lb-pip' }],
                envVMs: [{ name: 'WebServer-01', os: 'ubuntu' }, { name: 'WebServer-02', os: 'ubuntu' }],
                envNotes: 'Two web servers are pre-configured with a sample app.',
                tasks: [
                    {
                        name: 'Configure the Load Balancer',
                        activities: [
                            { title: 'Create backend pool', instructions: 'Add both web server VMs to the load balancer backend pool.' },
                            { title: 'Configure health probe', instructions: 'Create an HTTP health probe on port 80 with a 5-second interval.' },
                            { title: 'Create load balancing rule', instructions: 'Add a rule to distribute TCP port 80 traffic across the backend pool.' },
                        ],
                    },
                    {
                        name: 'Test Traffic Distribution',
                        activities: [
                            { title: 'Access the load balancer', instructions: 'Open the load balancer public IP in a browser and refresh multiple times.' },
                            { title: 'Verify distribution', instructions: 'Observe the server name changing in responses to confirm round-robin distribution.' },
                        ],
                    },
                ],
            },
        ],
        'DNS & Domain Management': [
            {
                title: 'Configure DNS Zones and Records',
                description: 'Create a DNS zone, add A, CNAME, and MX records, and verify name resolution.',
                duration: 30,
                difficulty: 'beginner',
                scoring: ['task-completion', 'quiz'],
                envResources: [{ type: 'DNS Zone', name: 'lab.example.com' }],
                envVMs: [],
                envNotes: 'DNS zone is pre-created.',
                tasks: [
                    {
                        name: 'Manage DNS Records',
                        activities: [
                            { title: 'Create DNS records', instructions: 'Add an A record, a CNAME record, and an MX record to the DNS zone.' },
                            { title: 'Verify resolution', instructions: 'Use nslookup or dig to verify each record resolves correctly.' },
                        ],
                    },
                ],
            },
        ],
        'VPN & Connectivity': [
            {
                title: 'Configure Hybrid Connectivity with VPN',
                description: 'Set up a site-to-site VPN gateway to establish secure connectivity between on-premises and cloud networks.',
                duration: 50,
                difficulty: 'advanced',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'VPN Gateway', name: 'lab-vpngw-01' }, { type: 'Local Network Gateway', name: 'lab-lng-01' }],
                envVMs: [{ name: 'OnPrem-Router', os: 'ubuntu' }],
                envNotes: 'Simulated on-premises environment is pre-configured.',
                tasks: [
                    {
                        name: 'Configure the VPN Gateway',
                        activities: [
                            { title: 'Create the gateway subnet', instructions: 'Add a GatewaySubnet to the virtual network.' },
                            { title: 'Deploy the VPN gateway', instructions: 'Create a VPN gateway and configure its public IP.' },
                            { title: 'Create the connection', instructions: 'Establish the site-to-site connection with the shared key.' },
                        ],
                    },
                    {
                        name: 'Verify Connectivity',
                        activities: [
                            { title: 'Check connection status', instructions: 'Verify the VPN connection status shows "Connected" in the portal.' },
                            { title: 'Test traffic flow', instructions: 'Ping resources across the VPN tunnel to confirm end-to-end connectivity.' },
                        ],
                    },
                ],
            },
        ],
        'CDN & Caching': [
            {
                title: 'Set Up Content Delivery and Caching',
                description: 'Configure a CDN profile and endpoint, set caching rules, and verify content is served from edge locations.',
                duration: 30,
                difficulty: 'intermediate',
                scoring: ['task-completion', 'quiz'],
                envResources: [{ type: 'CDN Profile', name: 'lab-cdn-01' }, { type: 'Storage Account', name: 'labcdnstor01' }],
                envVMs: [],
                envNotes: 'Storage account with static content is pre-provisioned.',
                tasks: [
                    {
                        name: 'Configure CDN',
                        activities: [
                            { title: 'Create CDN endpoint', instructions: 'Create a CDN endpoint pointing to the storage account origin.' },
                            { title: 'Configure caching rules', instructions: 'Set cache expiration rules for different content types.' },
                            { title: 'Test delivery', instructions: 'Access content via the CDN URL and verify cache headers.' },
                        ],
                    },
                ],
            },
        ],
        'Network Security Groups': [
            {
                title: 'Secure Network Traffic with Security Groups',
                description: 'Create and configure network security groups to control inbound and outbound traffic to cloud resources.',
                duration: 35,
                difficulty: 'beginner',
                scoring: ['resource-validation', 'script-check'],
                envResources: [{ type: 'NSG', name: 'lab-nsg-01' }, { type: 'NSG', name: 'lab-nsg-02' }],
                envVMs: [{ name: 'WebServer', os: 'ubuntu' }, { name: 'AppServer', os: 'ubuntu' }],
                envNotes: 'Two VMs are deployed with default-allow rules.',
                tasks: [
                    {
                        name: 'Configure Inbound Rules',
                        activities: [
                            { title: 'Allow HTTP/HTTPS to WebServer', instructions: 'Create inbound rules on lab-nsg-01 to allow ports 80 and 443 from any source.' },
                            { title: 'Deny direct access to AppServer', instructions: 'Create a deny rule on lab-nsg-02 blocking all inbound internet traffic.' },
                            { title: 'Allow internal traffic', instructions: 'Add a rule allowing traffic from the web subnet to the app subnet on port 8080.' },
                        ],
                    },
                    {
                        name: 'Test and Verify',
                        activities: [
                            { title: 'Test allowed traffic', instructions: 'Verify you can access the WebServer on port 80 from your browser.' },
                            { title: 'Test denied traffic', instructions: 'Confirm that direct access to AppServer from the internet is blocked.' },
                        ],
                    },
                ],
            },
        ],
        'Identity & Access Management': [
            {
                title: 'Configure Identity and Role-Based Access',
                description: 'Set up users, groups, and role assignments to implement least-privilege access to cloud resources.',
                duration: 40,
                difficulty: 'intermediate',
                scoring: ['task-completion', 'quiz'],
                envResources: [{ type: 'Resource Group', name: 'lab-rg-iam' }],
                envVMs: [],
                envNotes: 'A dedicated resource group is pre-created for access testing.',
                tasks: [
                    {
                        name: 'Create Users and Groups',
                        activities: [
                            { title: 'Create test users', instructions: 'Create two users: DevUser and ViewerUser in the directory.' },
                            { title: 'Create a security group', instructions: 'Create a "Developers" group and add DevUser as a member.' },
                        ],
                    },
                    {
                        name: 'Assign Roles',
                        activities: [
                            { title: 'Assign Contributor role', instructions: 'Assign the Contributor role to the Developers group on the resource group.' },
                            { title: 'Assign Reader role', instructions: 'Assign the Reader role to ViewerUser on the resource group.' },
                            { title: 'Test access', instructions: 'Sign in as each user and verify they have the expected permissions.' },
                        ],
                    },
                ],
            },
        ],
        'Key Vault & Secrets': [
            {
                title: 'Manage Secrets with Key Vault',
                description: 'Create a key vault, store and retrieve secrets, manage access policies, and integrate with an application.',
                duration: 35,
                difficulty: 'intermediate',
                scoring: ['script-check', 'task-completion'],
                envResources: [{ type: 'Key Vault', name: 'lab-kv-01' }],
                envVMs: [],
                envNotes: 'Key Vault is pre-provisioned with default access policies.',
                tasks: [
                    {
                        name: 'Store and Manage Secrets',
                        activities: [
                            { title: 'Create secrets', instructions: 'Add database connection string and API key secrets to the vault.' },
                            { title: 'Configure access policies', instructions: 'Grant an application identity permission to read secrets.' },
                            { title: 'Retrieve a secret', instructions: 'Use the CLI or SDK to retrieve and display a secret value.' },
                        ],
                    },
                ],
            },
        ],
        'Security Center & Compliance': [
            {
                title: 'Implement Security Monitoring and Compliance',
                description: 'Enable security center, review security recommendations, configure alerts, and assess compliance posture.',
                duration: 40,
                difficulty: 'intermediate',
                scoring: ['task-completion', 'screenshot'],
                envResources: [{ type: 'Resource Group', name: 'lab-rg-security' }],
                envVMs: [{ name: 'InsecureVM', os: 'windows-server' }],
                envNotes: 'A deliberately misconfigured VM is deployed for remediation exercises.',
                tasks: [
                    {
                        name: 'Review Security Posture',
                        activities: [
                            { title: 'Enable enhanced security', instructions: 'Enable the enhanced security plan for the subscription.' },
                            { title: 'Review recommendations', instructions: 'Navigate to the recommendations page and identify high-severity items.' },
                        ],
                    },
                    {
                        name: 'Remediate Issues',
                        activities: [
                            { title: 'Apply a recommendation', instructions: 'Select a recommendation and follow the remediation steps.' },
                            { title: 'Verify improvement', instructions: 'Check the secure score to confirm it improved after remediation.' },
                        ],
                    },
                ],
            },
        ],
        'Encryption & Data Protection': [
            {
                title: 'Implement Encryption and Data Protection',
                description: 'Enable encryption for storage and VMs, configure TLS, and manage encryption keys.',
                duration: 35,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'Storage Account', name: 'labencryptstor01' }, { type: 'Key Vault', name: 'lab-kv-encrypt' }],
                envVMs: [{ name: 'EncryptVM', os: 'windows-server' }],
                envNotes: 'Resources are deployed without encryption for the learner to enable.',
                tasks: [
                    {
                        name: 'Configure Encryption',
                        activities: [
                            { title: 'Enable storage encryption', instructions: 'Configure customer-managed keys for storage account encryption using Key Vault.' },
                            { title: 'Enable disk encryption', instructions: 'Enable disk encryption on the virtual machine using the key vault.' },
                            { title: 'Verify encryption status', instructions: 'Confirm encryption is enabled on all resources using the portal or CLI.' },
                        ],
                    },
                ],
            },
        ],
        'Blob & Object Storage': [
            {
                title: 'Work with Cloud Object Storage',
                description: 'Create storage accounts, upload and manage blobs, configure access tiers, and set up lifecycle policies.',
                duration: 35,
                difficulty: 'beginner',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'Storage Account', name: 'labstorage01' }],
                envVMs: [],
                envNotes: 'Storage account is pre-created.',
                tasks: [
                    {
                        name: 'Manage Blob Storage',
                        activities: [
                            { title: 'Create containers', instructions: 'Create two blob containers: "public-assets" and "private-data".' },
                            { title: 'Upload files', instructions: 'Upload sample files to each container using the portal or CLI.' },
                            { title: 'Configure access levels', instructions: 'Set the public-assets container to blob-level public access. Keep private-data private.' },
                        ],
                    },
                    {
                        name: 'Configure Lifecycle Management',
                        activities: [
                            { title: 'Create a lifecycle policy', instructions: 'Add a rule to move blobs to cool storage after 30 days and delete after 365 days.' },
                        ],
                    },
                ],
            },
        ],
        'File Storage': [
            {
                title: 'Configure Cloud File Shares',
                description: 'Create file shares, mount them to VMs, configure permissions, and set up file sync.',
                duration: 30,
                difficulty: 'beginner',
                scoring: ['task-completion', 'resource-validation'],
                envResources: [{ type: 'Storage Account', name: 'labfilestor01' }, { type: 'File Share', name: 'lab-share-01' }],
                envVMs: [{ name: 'FileClient', os: 'windows-server' }],
                envNotes: 'File share is pre-created. VM has SMB client ready.',
                tasks: [
                    {
                        name: 'Mount and Use File Shares',
                        activities: [
                            { title: 'Mount the file share', instructions: 'Use the portal to get the mount command and execute it on the VM.' },
                            { title: 'Create and access files', instructions: 'Create files on the mounted share and verify they appear in the portal.' },
                        ],
                    },
                ],
            },
        ],
        'Disk Management': [
            {
                title: 'Manage Virtual Machine Disks',
                description: 'Attach, resize, and snapshot managed disks on virtual machines.',
                duration: 30,
                difficulty: 'beginner',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'Managed Disk', name: 'lab-disk-01' }],
                envVMs: [{ name: 'DiskVM', os: 'windows-server' }],
                envNotes: 'VM is deployed with only an OS disk.',
                tasks: [
                    {
                        name: 'Manage Disks',
                        activities: [
                            { title: 'Attach a data disk', instructions: 'Add a 64 GB managed data disk to the VM.' },
                            { title: 'Initialize and format', instructions: 'Inside the VM, initialize the disk and create a volume.' },
                            { title: 'Create a snapshot', instructions: 'Create a snapshot of the data disk for backup purposes.' },
                        ],
                    },
                ],
            },
        ],
        'User & Group Management': [
            {
                title: 'Manage Users, Groups, and Directory Objects',
                description: 'Create and manage user accounts, security groups, and organizational units in a cloud directory.',
                duration: 35,
                difficulty: 'beginner',
                scoring: ['task-completion', 'quiz'],
                envResources: [{ type: 'Directory', name: 'Lab Directory' }],
                envVMs: [],
                envNotes: 'A test directory is pre-configured.',
                tasks: [
                    {
                        name: 'Manage Users and Groups',
                        activities: [
                            { title: 'Create user accounts', instructions: 'Create three user accounts with different roles.' },
                            { title: 'Create security groups', instructions: 'Create groups for IT, HR, and Finance departments.' },
                            { title: 'Assign users to groups', instructions: 'Add each user to the appropriate group.' },
                        ],
                    },
                ],
            },
        ],
        'Multi-Factor Authentication': [
            {
                title: 'Enable and Configure Multi-Factor Authentication',
                description: 'Set up MFA policies, configure conditional access, and test authentication flows.',
                duration: 30,
                difficulty: 'intermediate',
                scoring: ['task-completion', 'screenshot'],
                envResources: [{ type: 'Conditional Access Policy', name: 'lab-mfa-policy' }],
                envVMs: [],
                envNotes: 'Test users are pre-created.',
                tasks: [
                    {
                        name: 'Configure MFA',
                        activities: [
                            { title: 'Enable MFA for users', instructions: 'Enable per-user MFA for the test accounts.' },
                            { title: 'Create conditional access policy', instructions: 'Create a policy requiring MFA for all cloud app access.' },
                            { title: 'Test MFA flow', instructions: 'Sign in as a test user and complete the MFA setup and verification.' },
                        ],
                    },
                ],
            },
        ],
        'Single Sign-On': [
            {
                title: 'Configure Single Sign-On for Applications',
                description: 'Register an application, configure SSO with SAML or OIDC, and test the sign-on flow.',
                duration: 40,
                difficulty: 'advanced',
                scoring: ['task-completion', 'screenshot'],
                envResources: [{ type: 'App Registration', name: 'lab-sso-app' }],
                envVMs: [],
                envNotes: 'A sample application is pre-deployed for SSO configuration.',
                tasks: [
                    {
                        name: 'Configure SSO',
                        activities: [
                            { title: 'Register the application', instructions: 'Register the app in the identity provider and configure redirect URIs.' },
                            { title: 'Configure SAML/OIDC', instructions: 'Set up the SSO configuration with the appropriate protocol settings.' },
                            { title: 'Test sign-on', instructions: 'Access the application and verify SSO works without additional password prompts.' },
                        ],
                    },
                ],
            },
        ],
        'Relational Databases': [
            {
                title: 'Deploy and Manage a Cloud SQL Database',
                description: 'Provision a managed relational database, configure firewall rules, connect from an application, and set up backups.',
                duration: 45,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'script-check'],
                envResources: [{ type: 'SQL Database', name: 'lab-sqldb-01' }, { type: 'SQL Server', name: 'lab-sqlsrv-01' }],
                envVMs: [{ name: 'AppVM', os: 'windows-11' }],
                envNotes: 'SQL Management Studio is pre-installed on AppVM.',
                tasks: [
                    {
                        name: 'Provision the Database',
                        activities: [
                            { title: 'Create the database server', instructions: 'Deploy a managed SQL server with administrator credentials.' },
                            { title: 'Create a database', instructions: 'Create a new database with the standard tier.' },
                            { title: 'Configure firewall rules', instructions: 'Add your client IP and the AppVM IP to the server firewall rules.' },
                        ],
                    },
                    {
                        name: 'Connect and Query',
                        activities: [
                            { title: 'Connect from AppVM', instructions: 'Open SQL Management Studio and connect to the database.' },
                            { title: 'Run sample queries', instructions: 'Create a table, insert sample data, and run SELECT queries.' },
                        ],
                    },
                ],
            },
        ],
        'NoSQL Databases': [
            {
                title: 'Work with NoSQL Databases in the Cloud',
                description: 'Create a NoSQL database, design collections or tables, insert documents, and query data.',
                duration: 40,
                difficulty: 'intermediate',
                scoring: ['script-check', 'task-completion'],
                envResources: [{ type: 'NoSQL Account', name: 'lab-nosql-01' }],
                envVMs: [],
                envNotes: 'NoSQL account is pre-provisioned.',
                tasks: [
                    {
                        name: 'Create and Query Data',
                        activities: [
                            { title: 'Create a database and collection', instructions: 'Set up a database with a collection and configure the partition key.' },
                            { title: 'Insert documents', instructions: 'Insert sample JSON documents using the portal or SDK.' },
                            { title: 'Run queries', instructions: 'Execute queries to filter, sort, and aggregate the data.' },
                        ],
                    },
                ],
            },
        ],
        'Database Migration': [
            {
                title: 'Migrate a Database to the Cloud',
                description: 'Assess an on-premises database, plan the migration, execute it using a migration service, and validate the results.',
                duration: 50,
                difficulty: 'advanced',
                scoring: ['task-completion', 'resource-validation'],
                envResources: [{ type: 'Migration Service', name: 'lab-dms-01' }, { type: 'SQL Database', name: 'lab-target-db' }],
                envVMs: [{ name: 'OnPremDB', os: 'windows-server' }],
                envNotes: 'Source database is pre-populated on OnPremDB VM.',
                tasks: [
                    {
                        name: 'Assess and Migrate',
                        activities: [
                            { title: 'Run assessment', instructions: 'Use the migration assessment tool to identify compatibility issues.' },
                            { title: 'Configure migration', instructions: 'Set up the migration service with source and target connections.' },
                            { title: 'Execute migration', instructions: 'Start the migration and monitor progress.' },
                            { title: 'Validate results', instructions: 'Compare record counts and run test queries on the target database.' },
                        ],
                    },
                ],
            },
        ],
        'CI/CD Pipelines': [
            {
                title: 'Build a CI/CD Pipeline',
                description: 'Create a build pipeline, configure automated tests, and set up a release pipeline to deploy to cloud resources.',
                duration: 50,
                difficulty: 'intermediate',
                scoring: ['task-completion', 'screenshot'],
                envResources: [{ type: 'DevOps Project', name: 'lab-devops-01' }, { type: 'App Service', name: 'lab-cicd-app' }],
                envVMs: [],
                envNotes: 'A sample repo with code and tests is pre-configured.',
                tasks: [
                    {
                        name: 'Create the Pipeline',
                        activities: [
                            { title: 'Create build pipeline', instructions: 'Set up a YAML-based build pipeline that compiles the code and runs tests.' },
                            { title: 'Add release stage', instructions: 'Add a deployment stage that deploys to the App Service.' },
                            { title: 'Trigger and verify', instructions: 'Push a change and verify the full pipeline executes successfully.' },
                        ],
                    },
                ],
            },
        ],
        'Infrastructure as Code': [
            {
                title: 'Deploy Infrastructure as Code',
                description: 'Write and deploy infrastructure templates to provision cloud resources declaratively.',
                duration: 45,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'script-check'],
                envResources: [{ type: 'Resource Group', name: 'lab-rg-iac' }],
                envVMs: [{ name: 'DevVM', os: 'ubuntu' }],
                envNotes: 'Template tools (Terraform/CLI) are pre-installed on DevVM.',
                tasks: [
                    {
                        name: 'Write and Deploy Templates',
                        activities: [
                            { title: 'Write a template', instructions: 'Create a template that defines a storage account and virtual network.' },
                            { title: 'Deploy the template', instructions: 'Execute the deployment using the CLI.' },
                            { title: 'Verify resources', instructions: 'Confirm the resources were created with the expected configuration.' },
                            { title: 'Modify and redeploy', instructions: 'Update the template to add a subnet and redeploy.' },
                        ],
                    },
                ],
            },
        ],
        'Source Control': [
            {
                title: 'Work with Git and Source Control',
                description: 'Initialize repositories, manage branches, handle merge conflicts, and collaborate using pull requests.',
                duration: 35,
                difficulty: 'beginner',
                scoring: ['task-completion', 'quiz'],
                envResources: [{ type: 'Git Repository', name: 'lab-repo-01' }],
                envVMs: [{ name: 'DevVM', os: 'ubuntu' }],
                envNotes: 'Git is pre-installed on DevVM. A sample repo is available.',
                tasks: [
                    {
                        name: 'Git Fundamentals',
                        activities: [
                            { title: 'Clone and branch', instructions: 'Clone the repository and create a feature branch.' },
                            { title: 'Make changes and commit', instructions: 'Edit files, stage changes, and commit with a descriptive message.' },
                            { title: 'Create a pull request', instructions: 'Push the branch and open a pull request for review.' },
                        ],
                    },
                ],
            },
        ],
        'Configuration Management': [
            {
                title: 'Automate Server Configuration',
                description: 'Use configuration management tools to automate server setup, install software, and enforce desired state.',
                duration: 45,
                difficulty: 'intermediate',
                scoring: ['script-check', 'task-completion'],
                envResources: [{ type: 'Configuration', name: 'lab-config-01' }],
                envVMs: [{ name: 'ConfigServer', os: 'ubuntu' }, { name: 'TargetNode', os: 'ubuntu' }],
                envNotes: 'Configuration tool is pre-installed on ConfigServer.',
                tasks: [
                    {
                        name: 'Configure Servers',
                        activities: [
                            { title: 'Write a configuration', instructions: 'Create a playbook/manifest to install and configure a web server.' },
                            { title: 'Apply the configuration', instructions: 'Run the configuration against the TargetNode.' },
                            { title: 'Verify the result', instructions: 'Confirm the web server is running and serving the expected content.' },
                        ],
                    },
                ],
            },
        ],
        'Monitoring & Alerts': [
            {
                title: 'Configure Monitoring and Alerts',
                description: 'Set up monitoring for cloud resources, create alert rules, and configure notification channels.',
                duration: 35,
                difficulty: 'intermediate',
                scoring: ['task-completion', 'screenshot'],
                envResources: [{ type: 'Monitor Workspace', name: 'lab-monitor-ws' }],
                envVMs: [{ name: 'MonitoredVM', os: 'ubuntu' }],
                envNotes: 'Monitoring agent is pre-installed on MonitoredVM.',
                tasks: [
                    {
                        name: 'Set Up Monitoring',
                        activities: [
                            { title: 'Create alert rules', instructions: 'Create a metric alert for CPU usage exceeding 80% on the VM.' },
                            { title: 'Configure action group', instructions: 'Create an action group with email notification.' },
                            { title: 'Create a dashboard', instructions: 'Build a monitoring dashboard with CPU, memory, and disk widgets.' },
                        ],
                    },
                ],
            },
        ],
        'Log Analytics': [
            {
                title: 'Analyze Logs with Log Analytics',
                description: 'Configure log collection, write queries to analyze log data, and create visualizations.',
                duration: 40,
                difficulty: 'intermediate',
                scoring: ['task-completion', 'quiz'],
                envResources: [{ type: 'Log Analytics Workspace', name: 'lab-law-01' }],
                envVMs: [{ name: 'LogSource-VM', os: 'ubuntu' }],
                envNotes: 'Log collection agent is pre-configured.',
                tasks: [
                    {
                        name: 'Query and Analyze Logs',
                        activities: [
                            { title: 'Write log queries', instructions: 'Use the query language to search for specific events in the collected logs.' },
                            { title: 'Create visualizations', instructions: 'Convert query results into charts and pin them to a dashboard.' },
                        ],
                    },
                ],
            },
        ],
        'Cost Management': [
            {
                title: 'Manage Cloud Costs and Budgets',
                description: 'Analyze cloud spending, create budgets, configure cost alerts, and identify optimization opportunities.',
                duration: 30,
                difficulty: 'beginner',
                scoring: ['task-completion', 'quiz'],
                envResources: [],
                envVMs: [],
                envNotes: 'Lab subscription has sample cost data pre-populated.',
                tasks: [
                    {
                        name: 'Analyze and Control Costs',
                        activities: [
                            { title: 'Review cost analysis', instructions: 'Navigate to cost management and review spending by service and resource group.' },
                            { title: 'Create a budget', instructions: 'Create a monthly budget with an alert at 80% threshold.' },
                            { title: 'Identify savings', instructions: 'Review advisor recommendations for cost optimization.' },
                        ],
                    },
                ],
            },
        ],
        'Resource Organization': [
            {
                title: 'Organize Cloud Resources with Tags and Groups',
                description: 'Create resource groups, apply a tagging strategy, and use management groups for multi-subscription governance.',
                duration: 25,
                difficulty: 'beginner',
                scoring: ['task-completion', 'resource-validation'],
                envResources: [{ type: 'Resource Group', name: 'lab-rg-org-01' }, { type: 'Resource Group', name: 'lab-rg-org-02' }],
                envVMs: [],
                envNotes: 'Sample resources are pre-deployed across two resource groups.',
                tasks: [
                    {
                        name: 'Organize Resources',
                        activities: [
                            { title: 'Apply tags', instructions: 'Apply Environment, CostCenter, and Owner tags to all resources in the groups.' },
                            { title: 'Move resources', instructions: 'Move a resource from one resource group to another.' },
                            { title: 'Query by tags', instructions: 'Use the CLI to list all resources with a specific tag value.' },
                        ],
                    },
                ],
            },
        ],
        'Policy & Blueprints': [
            {
                title: 'Enforce Governance with Policies',
                description: 'Create and assign policies to enforce naming conventions, allowed regions, and required tags on cloud resources.',
                duration: 35,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'Resource Group', name: 'lab-rg-policy' }],
                envVMs: [],
                envNotes: 'Resource group is pre-created for policy testing.',
                tasks: [
                    {
                        name: 'Create and Test Policies',
                        activities: [
                            { title: 'Assign a built-in policy', instructions: 'Assign a policy that requires a specific tag on all resources.' },
                            { title: 'Test policy enforcement', instructions: 'Try creating a resource without the required tag and observe the denial.' },
                            { title: 'Create a custom policy', instructions: 'Write a custom policy to restrict allowed VM sizes.' },
                        ],
                    },
                ],
            },
        ],
        'Backup & Recovery': [
            {
                title: 'Configure Backup and Disaster Recovery',
                description: 'Set up backup policies, configure recovery vaults, perform backup and restore operations.',
                duration: 40,
                difficulty: 'intermediate',
                scoring: ['resource-validation', 'task-completion'],
                envResources: [{ type: 'Recovery Vault', name: 'lab-vault-01' }],
                envVMs: [{ name: 'BackupVM', os: 'windows-server' }],
                envNotes: 'VM has sample data pre-loaded for backup testing.',
                tasks: [
                    {
                        name: 'Configure and Test Backup',
                        activities: [
                            { title: 'Create a backup policy', instructions: 'Configure a daily backup policy with 30-day retention.' },
                            { title: 'Enable VM backup', instructions: 'Enable backup for the VM using the recovery vault.' },
                            { title: 'Perform a backup', instructions: 'Trigger an on-demand backup and monitor its progress.' },
                            { title: 'Restore from backup', instructions: 'Perform a file-level restore to recover a deleted file.' },
                        ],
                    },
                ],
            },
        ],
    };

    // ---- Public API ----
    function getDomains() {
        return domains;
    }

    function getLabTemplatesForSkill(skillName) {
        return labTemplates[skillName] || [];
    }

    function getEnvironmentPreset(platform) {
        return envPresets[platform] || envPresets.azure;
    }

    function getScoringMethods() {
        return scoringMethods;
    }

    function getScoringMethod(id) {
        return scoringMethods[id] || null;
    }

    /**
     * Main entry: analyze a program description and return matched skills grouped by domain.
     */
    function analyzeProgram(description) {
        const platform = detectPlatform(description);
        const matched = matchSkills(description);
        // Group by domain
        const grouped = {};
        matched.forEach(m => {
            if (!grouped[m.domain]) {
                grouped[m.domain] = { domainName: m.domainName, skills: [] };
            }
            if (!grouped[m.domain].skills.find(s => s === m.skill)) {
                grouped[m.domain].skills.push(m.skill);
            }
        });
        return { platform, skillsByDomain: grouped };
    }

    /**
     * Generate lab outlines for a set of confirmed skills.
     * Returns an array of lab outline objects ready for review.
     */
    function generateLabOutlines(skills, platform) {
        const preset = getEnvironmentPreset(platform);
        const outlines = [];

        skills.forEach(skillName => {
            const templates = getLabTemplatesForSkill(skillName);
            templates.forEach(tpl => {
                const outline = {
                    enabled: true,
                    skillName,
                    title: tpl.title,
                    description: tpl.description,
                    duration: tpl.duration,
                    difficulty: tpl.difficulty,
                    platform: preset.platform,
                    scoring: tpl.scoring.map(id => ({ id, ...getScoringMethod(id) })),
                    environment: {
                        vms: [...(preset.baseVMs || []), ...(tpl.envVMs || [])],
                        cloudResources: tpl.envResources || [],
                        credentials: preset.credentials,
                        notes: tpl.envNotes || '',
                    },
                    tasks: tpl.tasks,
                };
                // Deduplicate VMs by name
                const seen = new Set();
                outline.environment.vms = outline.environment.vms.filter(vm => {
                    if (seen.has(vm.name)) return false;
                    seen.add(vm.name);
                    return true;
                });
                outlines.push(outline);
            });
        });

        return outlines;
    }

    /**
     * Consolidate environments from all enabled outlines into a single unified environment.
     * Deduplicates VMs by name and cloud resources by type+name.
     */
    function buildUnifiedEnvironment(outlines, platform) {
        const preset = getEnvironmentPreset(platform);
        const vmMap = new Map();
        const resourceMap = new Map();

        // Always include base VMs from preset
        (preset.baseVMs || []).forEach(vm => {
            vmMap.set(vm.name, vm);
        });

        outlines.forEach(outline => {
            (outline.environment.vms || []).forEach(vm => {
                if (!vmMap.has(vm.name)) vmMap.set(vm.name, vm);
            });
            (outline.environment.cloudResources || []).forEach(res => {
                const key = `${res.type}::${res.name}`;
                if (!resourceMap.has(key)) resourceMap.set(key, res);
            });
        });

        return {
            platform,
            vms: Array.from(vmMap.values()),
            cloudResources: Array.from(resourceMap.values()),
            credentials: preset.credentials,
            notes: `Unified environment for ${outlines.length} labs. All labs share this base environment.`,
        };
    }

    /**
     * Generate a PowerShell build script that provisions the unified environment.
     * The script is platform-aware and creates all VMs, networking, and cloud resources.
     */
    function generateBuildScript(unifiedEnv) {
        const platform = unifiedEnv.platform || 'azure';
        const vms = unifiedEnv.vms || [];
        const resources = unifiedEnv.cloudResources || [];

        const lines = [];
        lines.push('#===============================================================================');
        lines.push('# Lab Environment Build Script');
        lines.push('# Auto-generated by Lab Program Designer');
        lines.push(`# Platform: ${platformDisplayName(platform)}`);
        lines.push(`# VMs: ${vms.length}  |  Cloud Resources: ${resources.length}`);
        lines.push('#===============================================================================');
        lines.push('');
        lines.push('param(');
        lines.push('    [string]$LabInstanceId = $env:LabInstance_Id,');
        lines.push('    [string]$ResourceGroupName = "lab-rg-$LabInstanceId"');
        lines.push(')');
        lines.push('');
        lines.push('$ErrorActionPreference = "Stop"');
        lines.push('');

        if (platform === 'azure') {
            lines.push(...buildAzureScript(vms, resources));
        } else if (platform === 'aws') {
            lines.push(...buildAwsScript(vms, resources));
        } else if (platform === 'gcp') {
            lines.push(...buildGcpScript(vms, resources));
        } else {
            lines.push(...buildAzureScript(vms, resources));
        }

        lines.push('');
        lines.push('#===============================================================================');
        lines.push('# Build Complete');
        lines.push('#===============================================================================');
        lines.push('Write-Host ""');
        lines.push('Write-Host "========================================" -ForegroundColor Green');
        lines.push('Write-Host " Environment build complete." -ForegroundColor Green');
        lines.push('Write-Host "========================================" -ForegroundColor Green');

        return lines.join('\r\n');
    }

    function platformDisplayName(p) {
        const map = { azure: 'Microsoft Azure', aws: 'Amazon Web Services', gcp: 'Google Cloud Platform', multi: 'Multi-Cloud' };
        return map[p] || p;
    }

    // ---- Azure Build Script ----
    function buildAzureScript(vms, resources) {
        const lines = [];

        // Authentication
        lines.push('#---------------------------------------');
        lines.push('# 1. Authenticate to Azure');
        lines.push('#---------------------------------------');
        lines.push('Write-Host "Authenticating to Azure..." -ForegroundColor Cyan');
        lines.push('');
        lines.push('$azContext = Get-AzContext -ErrorAction SilentlyContinue');
        lines.push('if (-not $azContext) {');
        lines.push('    Write-Host "No active Azure session. Logging in with lab credentials..." -ForegroundColor Yellow');
        lines.push('    $labUser = "@lab.CloudPortalCredential(User1).Username"');
        lines.push('    $labPass = "@lab.CloudPortalCredential(User1).Password" | ConvertTo-SecureString -AsPlainText -Force');
        lines.push('    $cred = New-Object System.Management.Automation.PSCredential($labUser, $labPass)');
        lines.push('    Connect-AzAccount -Credential $cred -TenantId "@lab.CloudSubscription.TenantId" | Out-Null');
        lines.push('}');
        lines.push('Write-Host "Authenticated successfully." -ForegroundColor Green');
        lines.push('');

        // Resource Group
        lines.push('#---------------------------------------');
        lines.push('# 2. Create Resource Group');
        lines.push('#---------------------------------------');
        lines.push('$location = "eastus"');
        lines.push('Write-Host "Creating Resource Group: $ResourceGroupName in $location..." -ForegroundColor Cyan');
        lines.push('New-AzResourceGroup -Name $ResourceGroupName -Location $location -Force | Out-Null');
        lines.push('Write-Host "Resource Group created." -ForegroundColor Green');
        lines.push('');

        // Networking
        lines.push('#---------------------------------------');
        lines.push('# 3. Create Virtual Network & Subnets');
        lines.push('#---------------------------------------');
        lines.push('$vnetName = "lab-vnet-$LabInstanceId"');
        lines.push('$subnetName = "lab-subnet-default"');
        lines.push('Write-Host "Creating Virtual Network: $vnetName..." -ForegroundColor Cyan');
        lines.push('');
        lines.push('$subnetConfig = New-AzVirtualNetworkSubnetConfig `');
        lines.push('    -Name $subnetName `');
        lines.push('    -AddressPrefix "10.0.1.0/24"');
        lines.push('');
        lines.push('$vnet = New-AzVirtualNetwork `');
        lines.push('    -ResourceGroupName $ResourceGroupName `');
        lines.push('    -Location $location `');
        lines.push('    -Name $vnetName `');
        lines.push('    -AddressPrefix "10.0.0.0/16" `');
        lines.push('    -Subnet $subnetConfig');
        lines.push('');
        lines.push('Write-Host "Virtual Network created." -ForegroundColor Green');
        lines.push('');

        // NSG
        lines.push('#---------------------------------------');
        lines.push('# 4. Create Network Security Group');
        lines.push('#---------------------------------------');
        lines.push('$nsgName = "lab-nsg-$LabInstanceId"');
        lines.push('Write-Host "Creating NSG: $nsgName..." -ForegroundColor Cyan');
        lines.push('');
        lines.push('$rdpRule = New-AzNetworkSecurityRuleConfig `');
        lines.push('    -Name "Allow-RDP" `');
        lines.push('    -Protocol Tcp `');
        lines.push('    -Direction Inbound `');
        lines.push('    -Priority 1000 `');
        lines.push('    -SourceAddressPrefix "*" `');
        lines.push('    -SourcePortRange "*" `');
        lines.push('    -DestinationAddressPrefix "*" `');
        lines.push('    -DestinationPortRange 3389 `');
        lines.push('    -Access Allow');
        lines.push('');
        lines.push('$sshRule = New-AzNetworkSecurityRuleConfig `');
        lines.push('    -Name "Allow-SSH" `');
        lines.push('    -Protocol Tcp `');
        lines.push('    -Direction Inbound `');
        lines.push('    -Priority 1001 `');
        lines.push('    -SourceAddressPrefix "*" `');
        lines.push('    -SourcePortRange "*" `');
        lines.push('    -DestinationAddressPrefix "*" `');
        lines.push('    -DestinationPortRange 22 `');
        lines.push('    -Access Allow');
        lines.push('');
        lines.push('$httpRule = New-AzNetworkSecurityRuleConfig `');
        lines.push('    -Name "Allow-HTTP" `');
        lines.push('    -Protocol Tcp `');
        lines.push('    -Direction Inbound `');
        lines.push('    -Priority 1002 `');
        lines.push('    -SourceAddressPrefix "*" `');
        lines.push('    -SourcePortRange "*" `');
        lines.push('    -DestinationAddressPrefix "*" `');
        lines.push('    -DestinationPortRange @("80","443") `');
        lines.push('    -Access Allow');
        lines.push('');
        lines.push('$nsg = New-AzNetworkSecurityGroup `');
        lines.push('    -ResourceGroupName $ResourceGroupName `');
        lines.push('    -Location $location `');
        lines.push('    -Name $nsgName `');
        lines.push('    -SecurityRules $rdpRule,$sshRule,$httpRule');
        lines.push('');
        lines.push('Write-Host "NSG created." -ForegroundColor Green');
        lines.push('');

        // Cloud Resources (storage, key vaults, etc.)
        const storageResources = resources.filter(r => /storage|blob|file/i.test(r.type));
        const kvResources = resources.filter(r => /key vault|secret/i.test(r.type));
        const dbResources = resources.filter(r => /sql|database|nosql|cosmos/i.test(r.type));
        const otherResources = resources.filter(r =>
            !/storage|blob|file|key vault|secret|sql|database|nosql|cosmos/i.test(r.type)
        );

        if (storageResources.length > 0) {
            lines.push('#---------------------------------------');
            lines.push('# 5. Create Storage Accounts');
            lines.push('#---------------------------------------');
            storageResources.forEach((res, idx) => {
                const saName = sanitizeAzName(res.name || `labstor${idx}`) + '$LabInstanceId'.slice(-4);
                lines.push(`Write-Host "Creating Storage Account: ${saName}..." -ForegroundColor Cyan`);
                lines.push(`New-AzStorageAccount \``);
                lines.push(`    -ResourceGroupName $ResourceGroupName \``);
                lines.push(`    -Name "${saName}" \``);
                lines.push(`    -Location $location \``);
                lines.push(`    -SkuName "Standard_LRS" \``);
                lines.push(`    -Kind "StorageV2" | Out-Null`);
                lines.push(`Write-Host "Storage Account ${saName} created." -ForegroundColor Green`);
                lines.push('');
            });
        }

        if (kvResources.length > 0) {
            lines.push('#---------------------------------------');
            lines.push('# 6. Create Key Vaults');
            lines.push('#---------------------------------------');
            kvResources.forEach((res, idx) => {
                const kvName = sanitizeAzName(res.name || `labkv${idx}`);
                lines.push(`Write-Host "Creating Key Vault: ${kvName}..." -ForegroundColor Cyan`);
                lines.push(`New-AzKeyVault \``);
                lines.push(`    -ResourceGroupName $ResourceGroupName \``);
                lines.push(`    -VaultName "${kvName}" \``);
                lines.push(`    -Location $location | Out-Null`);
                lines.push(`Write-Host "Key Vault ${kvName} created." -ForegroundColor Green`);
                lines.push('');
            });
        }

        if (dbResources.length > 0) {
            lines.push('#---------------------------------------');
            lines.push(`# ${storageResources.length > 0 || kvResources.length > 0 ? '7' : '5'}. Create Database Resources`);
            lines.push('#---------------------------------------');
            dbResources.forEach(res => {
                lines.push(`Write-Host "Placeholder: Create ${res.type} — ${res.name}" -ForegroundColor Yellow`);
                lines.push(`# TODO: Add provisioning commands for ${res.type}: ${res.name}`);
                lines.push('');
            });
        }

        // Other cloud resources as placeholders
        if (otherResources.length > 0) {
            lines.push('#---------------------------------------');
            lines.push('# Additional Cloud Resources');
            lines.push('#---------------------------------------');
            otherResources.forEach(res => {
                lines.push(`Write-Host "Placeholder: Create ${res.type} — ${res.name}" -ForegroundColor Yellow`);
                lines.push(`# TODO: Add provisioning commands for ${res.type}: ${res.name}`);
                lines.push('');
            });
        }

        // VM provisioning
        if (vms.length > 0) {
            lines.push('#---------------------------------------');
            lines.push('# Provision Virtual Machines');
            lines.push('#---------------------------------------');
            lines.push('$vmCredential = New-Object System.Management.Automation.PSCredential(');
            lines.push('    "LabUser",');
            lines.push('    ("Pa$$w0rd" | ConvertTo-SecureString -AsPlainText -Force)');
            lines.push(')');
            lines.push('$subnet = Get-AzVirtualNetworkSubnetConfig -Name $subnetName -VirtualNetwork $vnet');
            lines.push('');

            vms.forEach((vm, idx) => {
                const isLinux = (vm.os === 'ubuntu' || vm.os === 'centos');
                const imageRef = getAzureImageRef(vm.os);
                const vmName = vm.name || `LabVM-${idx + 1}`;

                lines.push(`# --- VM: ${vmName} (${vm.os}) ---`);
                lines.push(`Write-Host "Provisioning VM: ${vmName} (${vm.os})..." -ForegroundColor Cyan`);
                lines.push('');

                // NIC
                lines.push(`$pip${idx} = New-AzPublicIpAddress \``);
                lines.push(`    -ResourceGroupName $ResourceGroupName \``);
                lines.push(`    -Name "${vmName}-pip" \``);
                lines.push(`    -Location $location \``);
                lines.push(`    -AllocationMethod Static \``);
                lines.push(`    -Sku Standard | Out-Null`);
                lines.push('');
                lines.push(`$nic${idx} = New-AzNetworkInterface \``);
                lines.push(`    -ResourceGroupName $ResourceGroupName \``);
                lines.push(`    -Name "${vmName}-nic" \``);
                lines.push(`    -Location $location \``);
                lines.push(`    -SubnetId $subnet.Id \``);
                lines.push(`    -PublicIpAddressId $pip${idx}.Id \``);
                lines.push(`    -NetworkSecurityGroupId $nsg.Id`);
                lines.push('');

                // VM config
                lines.push(`$vmConfig${idx} = New-AzVMConfig \``);
                lines.push(`    -VMName "${vmName}" \``);
                lines.push(`    -VMSize "Standard_B2ms"`);
                lines.push('');

                if (isLinux) {
                    lines.push(`$vmConfig${idx} = Set-AzVMOperatingSystem \``);
                    lines.push(`    -VM $vmConfig${idx} \``);
                    lines.push(`    -Linux \``);
                    lines.push(`    -ComputerName "${vmName}" \``);
                    lines.push(`    -Credential $vmCredential`);
                } else {
                    lines.push(`$vmConfig${idx} = Set-AzVMOperatingSystem \``);
                    lines.push(`    -VM $vmConfig${idx} \``);
                    lines.push(`    -Windows \``);
                    lines.push(`    -ComputerName "${vmName}" \``);
                    lines.push(`    -Credential $vmCredential \``);
                    lines.push(`    -ProvisionVMAgent`);
                }
                lines.push('');
                lines.push(`$vmConfig${idx} = Set-AzVMSourceImage \``);
                lines.push(`    -VM $vmConfig${idx} \``);
                lines.push(`    -PublisherName "${imageRef.publisher}" \``);
                lines.push(`    -Offer "${imageRef.offer}" \``);
                lines.push(`    -Skus "${imageRef.sku}" \``);
                lines.push(`    -Version "latest"`);
                lines.push('');
                lines.push(`$vmConfig${idx} = Add-AzVMNetworkInterface \``);
                lines.push(`    -VM $vmConfig${idx} \``);
                lines.push(`    -Id $nic${idx}.Id`);
                lines.push('');
                lines.push(`New-AzVM \``);
                lines.push(`    -ResourceGroupName $ResourceGroupName \``);
                lines.push(`    -Location $location \``);
                lines.push(`    -VM $vmConfig${idx} | Out-Null`);
                lines.push('');
                lines.push(`Write-Host "VM ${vmName} provisioned successfully." -ForegroundColor Green`);
                lines.push('');
            });
        }

        // Summary
        lines.push('#---------------------------------------');
        lines.push('# Environment Summary');
        lines.push('#---------------------------------------');
        lines.push('Write-Host ""');
        lines.push('Write-Host "--- Environment Summary ---" -ForegroundColor Cyan');
        lines.push(`Write-Host "Resource Group : $ResourceGroupName"`);
        lines.push(`Write-Host "Virtual Network: $vnetName"`);
        lines.push(`Write-Host "NSG            : $nsgName"`);
        vms.forEach(vm => {
            lines.push(`Write-Host "VM             : ${vm.name} (${vm.os})"`);
        });
        resources.forEach(res => {
            lines.push(`Write-Host "Resource       : ${res.type} — ${res.name}"`);
        });

        return lines;
    }

    function getAzureImageRef(os) {
        const map = {
            'windows-server': { publisher: 'MicrosoftWindowsServer', offer: 'WindowsServer', sku: '2022-Datacenter' },
            'windows-11': { publisher: 'MicrosoftWindowsDesktop', offer: 'windows-11', sku: 'win11-22h2-pro' },
            'ubuntu': { publisher: 'Canonical', offer: '0001-com-ubuntu-server-jammy', sku: '22_04-lts-gen2' },
            'centos': { publisher: 'OpenLogic', offer: 'CentOS', sku: '8_5-gen2' },
            'custom': { publisher: 'MicrosoftWindowsDesktop', offer: 'windows-11', sku: 'win11-22h2-pro' },
        };
        return map[os] || map['windows-11'];
    }

    function sanitizeAzName(name) {
        return name.replace(/[^a-z0-9]/gi, '').toLowerCase().slice(0, 20);
    }

    // ---- AWS Build Script (placeholder) ----
    function buildAwsScript(vms, resources) {
        const lines = [];
        lines.push('#---------------------------------------');
        lines.push('# AWS Environment Build');
        lines.push('#---------------------------------------');
        lines.push('Write-Host "Configuring AWS environment..." -ForegroundColor Cyan');
        lines.push('');
        lines.push('# Authenticate');
        lines.push('Set-AWSCredential -AccessKey $env:AWS_ACCESS_KEY -SecretKey $env:AWS_SECRET_KEY');
        lines.push('Set-DefaultAWSRegion -Region "us-east-1"');
        lines.push('');

        // VPC
        lines.push('# Create VPC');
        lines.push('$vpc = New-EC2Vpc -CidrBlock "10.0.0.0/16"');
        lines.push('$subnet = New-EC2Subnet -VpcId $vpc.VpcId -CidrBlock "10.0.1.0/24"');
        lines.push('');

        vms.forEach((vm, idx) => {
            const isLinux = (vm.os === 'ubuntu' || vm.os === 'centos');
            lines.push(`# VM: ${vm.name}`);
            lines.push(`Write-Host "Launching EC2 instance: ${vm.name}..." -ForegroundColor Cyan`);
            lines.push(`# TODO: Specify AMI ID for ${vm.os}`);
            lines.push(`$instance${idx} = New-EC2Instance \``);
            lines.push(`    -ImageId "ami-placeholder-${vm.os}" \``);
            lines.push(`    -InstanceType "t3.medium" \``);
            lines.push(`    -SubnetId $subnet.SubnetId \``);
            lines.push(`    -MinCount 1 -MaxCount 1`);
            lines.push(`Write-Host "Instance ${vm.name} launched." -ForegroundColor Green`);
            lines.push('');
        });

        resources.forEach(res => {
            lines.push(`# Resource: ${res.type} — ${res.name}`);
            lines.push(`Write-Host "Placeholder: Create ${res.type} — ${res.name}" -ForegroundColor Yellow`);
            lines.push(`# TODO: Add AWS provisioning for ${res.type}`);
            lines.push('');
        });

        return lines;
    }

    // ---- GCP Build Script (placeholder) ----
    function buildGcpScript(vms, resources) {
        const lines = [];
        lines.push('#---------------------------------------');
        lines.push('# GCP Environment Build');
        lines.push('#---------------------------------------');
        lines.push('Write-Host "Configuring GCP environment..." -ForegroundColor Cyan');
        lines.push('');
        lines.push('$projectId = "lab-project-$LabInstanceId"');
        lines.push('$zone = "us-central1-a"');
        lines.push('');

        vms.forEach((vm, idx) => {
            const isLinux = (vm.os === 'ubuntu' || vm.os === 'centos');
            lines.push(`# VM: ${vm.name}`);
            lines.push(`Write-Host "Creating GCE instance: ${vm.name}..." -ForegroundColor Cyan`);
            lines.push(`# TODO: Use gcloud or GCP PowerShell module`);
            lines.push(`# gcloud compute instances create "${vm.name}" --zone=$zone --machine-type=e2-medium --image-family="${vm.os === 'ubuntu' ? 'ubuntu-2204-lts' : 'windows-2022'}" --image-project="${vm.os === 'ubuntu' ? 'ubuntu-os-cloud' : 'windows-cloud'}"`);
            lines.push(`Write-Host "Instance ${vm.name} created." -ForegroundColor Green`);
            lines.push('');
        });

        resources.forEach(res => {
            lines.push(`# Resource: ${res.type} — ${res.name}`);
            lines.push(`Write-Host "Placeholder: Create ${res.type} — ${res.name}" -ForegroundColor Yellow`);
            lines.push(`# TODO: Add GCP provisioning for ${res.type}`);
            lines.push('');
        });

        return lines;
    }

    /**
     * Adjust generated lab outlines based on density and target duration settings.
     * - light: keep only 1st template per skill, merge if under 20 min
     * - moderate: keep all (default behavior)
     * - heavy: split multi-task labs into separate focused labs
     * Also adjusts duration to approach the target.
     */
    function adjustOutlinesForDensity(outlines, density, targetDuration) {
        targetDuration = targetDuration || 45;
        let adjusted = outlines.map(o => ({ ...o })); // shallow copy

        if (density === 'light') {
            // Keep only the first lab per skill
            const seen = new Set();
            adjusted = adjusted.filter(o => {
                if (seen.has(o.skillName)) return false;
                seen.add(o.skillName);
                return true;
            });
            // Scale durations up toward target (longer labs)
            adjusted.forEach(o => {
                o.duration = Math.max(o.duration, targetDuration);
            });

        } else if (density === 'heavy') {
            // Split labs with 2+ tasks into separate labs (one per task)
            const expanded = [];
            adjusted.forEach(o => {
                if (o.tasks.length >= 2) {
                    o.tasks.forEach((task, ti) => {
                        expanded.push({
                            ...o,
                            title: `${o.title} — ${task.name}`,
                            description: `Focused lab: ${task.name}. ${o.description}`,
                            duration: Math.round(targetDuration * 0.8),
                            tasks: [task],
                        });
                    });
                } else {
                    expanded.push(o);
                }
            });
            adjusted = expanded;
            // Scale durations down toward target (shorter labs)
            adjusted.forEach(o => {
                o.duration = Math.min(o.duration, targetDuration);
            });

        } else {
            // Moderate — adjust duration toward target
            adjusted.forEach(o => {
                const ratio = targetDuration / 45; // 45 is the baseline
                o.duration = Math.round(o.duration * ratio);
                o.duration = Math.max(15, Math.min(120, o.duration));
            });
        }

        // Re-enable all
        adjusted.forEach(o => { o.enabled = true; });
        return adjusted;
    }

    /**
     * Returns a condensed text summary of the catalog suitable for injection
     * into AI system prompts. Kept under ~2000 tokens.
     */
    function toPromptContext() {
        const lines = [];

        // Skill domains
        lines.push('=== SKILL DOMAINS ===');
        domains.forEach(d => {
            lines.push(`${d.name}: ${d.skills.map(s => s.name).join(', ')}`);
        });

        // Lab template types
        lines.push('');
        lines.push('=== LAB TEMPLATE TYPES ===');
        Object.keys(labTemplates).forEach(skillName => {
            const tpls = labTemplates[skillName];
            tpls.forEach(t => {
                lines.push(`- ${t.title} (${t.difficulty}, ${t.duration}min): ${t.description}`);
            });
        });

        // Environment presets
        lines.push('');
        lines.push('=== ENVIRONMENT PRESETS ===');
        Object.keys(envPresets).forEach(key => {
            const p = envPresets[key];
            const vmDesc = p.baseVMs.length > 0
                ? `Base VMs: ${p.baseVMs.map(v => `${v.name} (${v.os})`).join(', ')}`
                : 'No base VMs';
            lines.push(`${platformDisplayName(key)}: ${vmDesc}. Credentials: ${p.credentials.split('\n')[0]}...`);
        });

        // Scoring methods
        lines.push('');
        lines.push('=== SCORING METHODS ===');
        Object.keys(scoringMethods).forEach(id => {
            const m = scoringMethods[id];
            lines.push(`- ${m.name}: ${m.description}`);
        });

        return lines.join('\n');
    }

    /**
     * Returns a structured text description of environment requirements
     * (VMs, cloud resources, credentials) based on platform and selected skills.
     * Intended for injection into Phase 4 AI prompts.
     */
    function generateBOMContext(platform, skills) {
        const preset = getEnvironmentPreset(platform);
        const lines = [];

        lines.push(`Platform: ${platformDisplayName(platform)}`);
        lines.push(`Credentials: ${preset.credentials}`);
        lines.push('');

        // Collect all VMs and cloud resources from matching templates
        const vmMap = new Map();
        const resourceMap = new Map();

        // Include base VMs from preset
        (preset.baseVMs || []).forEach(vm => {
            vmMap.set(vm.name, vm);
        });

        (skills || []).forEach(skillName => {
            const templates = getLabTemplatesForSkill(skillName);
            templates.forEach(tpl => {
                (tpl.envVMs || []).forEach(vm => {
                    if (!vmMap.has(vm.name)) vmMap.set(vm.name, vm);
                });
                (tpl.envResources || []).forEach(res => {
                    const key = `${res.type}::${res.name}`;
                    if (!resourceMap.has(key)) resourceMap.set(key, res);
                });
            });
        });

        // VMs
        const vms = Array.from(vmMap.values());
        lines.push(`=== VIRTUAL MACHINES (${vms.length}) ===`);
        if (vms.length === 0) {
            lines.push('No VMs required.');
        } else {
            vms.forEach(vm => {
                lines.push(`- ${vm.name}: OS=${vm.os}`);
            });
        }

        // Cloud resources
        const resources = Array.from(resourceMap.values());
        lines.push('');
        lines.push(`=== CLOUD RESOURCES (${resources.length}) ===`);
        if (resources.length === 0) {
            lines.push('No additional cloud resources required.');
        } else {
            resources.forEach(res => {
                lines.push(`- ${res.type}: ${res.name}`);
            });
        }

        // Environment notes from templates
        lines.push('');
        lines.push('=== ENVIRONMENT NOTES ===');
        (skills || []).forEach(skillName => {
            const templates = getLabTemplatesForSkill(skillName);
            templates.forEach(tpl => {
                if (tpl.envNotes) {
                    lines.push(`[${skillName}] ${tpl.envNotes}`);
                }
            });
        });

        return lines.join('\n');
    }

    return {
        getDomains,
        analyzeProgram,
        generateLabOutlines,
        adjustOutlinesForDensity,
        buildUnifiedEnvironment,
        generateBuildScript,
        getScoringMethods,
        getScoringMethod,
        detectPlatform,
        toPromptContext,
        getEnvironmentPreset,
        getLabTemplatesForSkill,
        generateBOMContext,
    };
})();
