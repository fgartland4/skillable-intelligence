"""Skillable self-knowledge — Layer 2.

This module is the single source of truth for what Skillable's platform can
do.  It sits between Layer 1 (customer / company intelligence, per-company
files in `backend/data/company_intel/`) and Layer 3 (scoring logic — the
per-pillar scorers, rubric grader, Fit Score composer, ACV calculator, etc.).

Layer 2 is *content*, not *rules*.  A capability here describes a Skillable
fabric, feature, or orchestration pattern.  Scoring rules that consume
capabilities (e.g. "apply the AWS supported-services list to grade this
product's provisioning") live in Layer 3 modules and import from this file.

History:
  - Pre-2026-04-16: Two parallel sources — `scoring_config.SKILLABLE_CAPABILITIES`
    (a terse Python tuple) and `knowledge/skillable_capabilities.json` (a
    richer JSON file that was loaded but never read).
  - 2026-04-16: JSON file retired, tuple kept in `scoring_config.py`.
  - 2026-04-17: Tuple extracted to this dedicated module and enriched.
    Actually consumed now — the researcher discovery prompt and the
    Pillar 1 labability fact extractor render capability context from this
    tuple at prompt-build time, so a single edit here changes what Claude
    sees on the next research call.

Design rule: if something here needs to know about a specific product,
customer, or scoring weight, it does not belong in this module.  Move it to
the consuming layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SkillableCapability:
    """A Skillable platform capability the AI and scorers should reference.

    The `name` + `description` pair is the canonical minimum.  The optional
    structured fields carry richer detail for fabrics / capabilities where
    the detail matters (e.g. AWS supported/unsupported services list).
    Entries that are conceptually simple leave the structured fields empty.

    `related_capabilities` holds the *names* of other entries this one
    references so consumers can follow the graph (e.g. Cloud Security Review
    references both Cloud Slice - AWS and Cloud Slice - Azure).
    """

    name: str
    description: str
    fabric: Optional[str] = None  # "azure" | "aws" | "datacenter" | "cross" | None
    supported_services: tuple[str, ...] = ()
    unsupported_services: tuple[str, ...] = ()
    considerations: tuple[tuple[str, str], ...] = ()  # (service/topic, note) pairs
    authoritative_catalog_url: Optional[str] = None
    setup_prerequisites: tuple[str, ...] = ()
    templates_supported: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    modes: tuple[str, ...] = ()
    related_capabilities: tuple[str, ...] = ()
    status: str = "current"  # "current" | "deprecated" | "preview"
    last_updated: Optional[str] = None  # ISO date of the authoritative source


# ═══════════════════════════════════════════════════════════════════════════════
# The capabilities
#
# Keep entries alphabetical within their conceptual group.  Groups are:
#   1. Virtualization fabrics (Datacenter, AWS Virtualization)
#   2. Cloud Slice fabrics (Azure, AWS)
#   3. Cross-fabric capabilities (Credential Pool, Security Review, Automated
#      Scoring, Hyper-V Preference, BIOS GUID Pinning, M365 Tenant
#      Provisioning, Simulations)
# ═══════════════════════════════════════════════════════════════════════════════

SKILLABLE_CAPABILITIES: tuple[SkillableCapability, ...] = (

    # ─────────────────────────────────────────────────────────────────────
    # Virtualization fabrics
    # ─────────────────────────────────────────────────────────────────────

    SkillableCapability(
        name="Skillable Datacenter",
        fabric="datacenter",
        description=(
            "Purpose-built for ephemeral learning and skill validation.  Three "
            "virtualization fabrics: Hyper-V (default — full control, custom "
            "networking, predictable launches), VMware ESX (use only when nested "
            "virtualization or socket licensing requires it), Docker (container-"
            "native workloads only).  Full custom network topologies: private "
            "networks, NAT, VPNs, dedicated IP addressing, network traffic "
            "monitoring.  No idle storage costs, no egress charges, no cloud "
            "throttling."
        ),
        related_capabilities=("Hyper-V Preference", "BIOS GUID Pinning"),
    ),

    SkillableCapability(
        name="AWS Virtualization",
        fabric="aws",
        description=(
            "Runs Virtual Machines using AWS EC2 as a Skillable VM fabric — "
            "distinct from Cloud Slice (Cloud Slice provisions isolated AWS "
            "accounts per learner; AWS Virtualization runs specific EC2 VMs "
            "inside a Skillable VM profile).  Supports existing AMIs, custom "
            "AMIs captured from modified EC2 instances, and imports from "
            "Hyper-V, Microsoft Azure, VMware, and Citrix via the AWS VM "
            "Import/Export service.  On lab save, EC2 resources are suspended "
            "and billing pauses; on resume, the instance reboots.  Uses Shared "
            "+ Manual Cloud Subscription Pool (distinct from Cloud Slice's "
            "Dedicated + Automated pattern)."
        ),
        modes=("Shared + Manual pool type",),
    ),

    # ─────────────────────────────────────────────────────────────────────
    # Cloud Slice fabrics
    # ─────────────────────────────────────────────────────────────────────

    SkillableCapability(
        name="Cloud Slice - Azure",
        fabric="azure",
        description=(
            "Provisions isolated Azure environments per learner.  ALL Azure "
            "services are supported after Security Review — the platform is "
            "fully integrated with Azure such that the security-review process "
            "(not a curated service list) is the gating mechanism.  Skillable "
            "is granted Global Administrator on the tenant and Owner on the "
            "subscription with all resource providers enabled; a Cloud Addendum "
            "is required on the customer contract.  Three IaC authoring paths: "
            "ARM JSON, Bicep (native DSL, compiles to ARM at launch, full "
            "parity), and Terraform (runs in a Docker container via a Life "
            "Cycle Action — for customers with existing Terraform investment, "
            "slower than ARM).  Resource Templates stored natively in Skillable "
            "Studio or externally (GitHub repo with anonymous read).  Access "
            "Control Policies restrict services, SKUs, names, regions, capacity "
            "— default is allow-all so ACPs must be written as deny-except "
            "whitelists; functions and ARM replacement tokens (e.g. "
            "resourceGroup().location, resourceGroup().tags.LabInstance) are "
            "supported inside ACPs.  Resource Providers must be registered per "
            "subscription before their services can be used; pre-registration, "
            "selective registration, or a custom 'Register Microsoft providers' "
            "role are the three supported patterns."
        ),
        authoritative_catalog_url="https://azure.microsoft.com/en-us/products",
        modes=(
            "CSR (resource-group-scoped — users restricted to given RGs)",
            "CSS (subscription-scoped — users can access subscription admin settings, create own RGs)",
        ),
        roles=("Reader", "Contributor", "Owner"),
        templates_supported=("ARM JSON", "Bicep", "Terraform (via LCA+Docker)"),
        setup_prerequisites=(
            "Dedicated Azure AD Tenant recommended (locked-down External "
            "Collaboration; allowlist skillable.com and learnondemandsystems.com)",
            "Cloud Addendum on contract",
            "Subscription-pool setup via PowerShell script run in Azure Cloud Shell",
            "Application registration configured as Owner on each subscription",
            "Skillable Studio Policy Set (Azure-side policy set — LCAs must not modify or remove)",
        ),
        considerations=(
            ("quota_planning", "Resource quota increases require a Microsoft "
             "support ticket; typical turnaround is hours but can take days or "
             "weeks for high-demand SKUs/regions.  Severity A requests are "
             "auto-downgraded to Severity B."),
            ("managed_acps", "Pre-approved 'Managed ACPs' exist — labs using "
             "only pre-approved ACPs skip the security review step."),
            ("bicep_editor", "Skillable Studio's Monaco editor treats Bicep as "
             "plain text (no syntax highlighting / IntelliSense / inline "
             "validation).  Author and validate Bicep locally before pasting."),
        ),
        related_capabilities=(
            "Cloud Security Review",
            "Cloud Credential Pool",
            "M365 Tenant Provisioning",
        ),
        last_updated="2025-04-04",
    ),

    SkillableCapability(
        name="Cloud Slice - AWS",
        fabric="aws",
        description=(
            "Provisions a dedicated, isolated AWS account per learner, drawn "
            "from a pre-provisioned pool.  The pool is automated + dedicated "
            "(contrast with AWS Virtualization's shared + manual pattern).  "
            "Unlike Azure Cloud Slice, not every AWS service is supported — "
            "Skillable maintains an explicit supported/unsupported list "
            "because some services can't be orchestrated under the per-learner "
            "organization-account pattern today.  Unsupported services are NOT "
            "red — they are AMBER: Skillable can add support on demand, there "
            "has simply not been demand yet.  The AWS Organization root "
            "account must be dedicated to Skillable (not an extension of a "
            "production AWS account) with billing set up; Skillable is granted "
            "AWSOrganizationsFullAccess + AdministratorAccess on the root IAM "
            "user.  Default org limit is 10 accounts (1 management + 9 members) "
            "— quota increases require an AWS support ticket (typical 24-hour "
            "response).  ACPs default DENY; lab ACPs whitelist specific "
            "resources using Action format 'y:*' or 'iam:GetRole'.  "
            "LabSecureAccess boundary policy + Lab Developer policy are "
            "automatically protected against removal by lab users.  Optional "
            "CloudTrail → CloudWatch → S3 → SFTP log transfer pipeline for "
            "audit / compliance (4-hour latency, per-lab-instance JSON files)."
        ),
        # Supported list — canonical names matching the Sept 2024 doc.  ~65 items.
        supported_services=(
            "Alexa for Business", "Amazon API Gateway", "Amazon Athena",
            "Amazon Access Analyzer", "Amazon Audit Manager",
            "Amazon Cloud Directory", "Amazon CloudSearch", "Amazon CloudWatch",
            "Amazon CloudWatch Events", "Amazon CloudWatch Logs",
            "Amazon CloudFront", "Amazon CloudShell", "Amazon Cognito User Pools",
            "Amazon Data Lifecycle Manager", "Amazon DynamoDB",
            "Amazon DynamoDB Accelerator (DAX)", "Amazon EC2",
            "Amazon EC2 Container Registry", "Amazon EC2 Container Service (ECS)",
            "Amazon Elastic Container Service for Kubernetes (EKS)",
            "Amazon Elastic File System", "Amazon Kinesis",
            "Amazon Kinesis Analytics", "Amazon Kinesis Firehose",
            "Amazon Kinesis Video Streams", "Amazon Machine Learning",
            "Amazon RDS", "Amazon Redshift", "Amazon Route 53", "Amazon SimpleDB",
            "Amazon SNS", "Amazon Simple Systems Manager (SSM)", "Amazon SQS",
            "AWS AppSync", "AWS Backup", "AWS Cloud9", "AWS CloudFormation",
            "AWS CloudTrail", "AWS Config", "AWS IoT Analytics", "AWS Lambda",
            "AWS Key Management Service (KMS)", "AWS OpsWorks",
            "AWS Resource Groups", "AWS Resource Group Tagging", "Amazon S3",
            "Amazon S3 Access points", "AWS Secrets Manager", "AWS Step Functions",
            "AWS WAF Classic", "AWS WAF v2", "AWS WAF Regional",
            "Auto Scaling Plans", "Elastic Load Balancing",
            "Elastic Load Balancing V2", "EventBridge",
            "EventBridge Scheduler", "EventBridge Pipes", "EventBridge Schema",
            "Identity And Access Management (IAM)", "Virtual Private Cloud (VPC)",
            "AWS Elastic Beanstalk", "AWS Glue",
        ),
        # NOT supported — the amber set.  ~75 items.
        unsupported_services=(
            "Amazon AppStream 2.0", "Amazon Chime", "Amazon Cognito Identity",
            "Amazon Cognito Sync", "Amazon Comprehend", "Amazon Connect",
            "Amazon Elastic MapReduce (EMR)", "Amazon Elastic Transcoder",
            "Amazon ElastiCache", "Amazon Elasticsearch Service",
            "Amazon FreeRTOS", "Amazon GameLift", "Amazon Glacier",
            "Amazon GuardDuty", "Amazon Inspector", "Amazon MQ", "Amazon Neptune",
            "Amazon Pinpoint", "Amazon Polly", "Amazon Lex", "Amazon Lightsail",
            "Amazon Rekognition", "Amazon Route 53 Auto Naming",
            "Amazon Route53 Domains", "Amazon SageMaker", "Amazon SES",
            "Amazon Simple Workflow Service (SWF)", "Amazon Sumerian",
            "Amazon Transcribe", "Amazon Translate", "Amazon WorkDocs",
            "Amazon WorkMail", "Amazon WorkSpaces",
            "Amazon WorkSpaces Application Manager", "AWS Artifact",
            "AWS Budget Service", "AWS Certificate Manager (ACM)",
            "AWS Certificate Manager Private Certificate Authority (ACM-PCA)",
            "AWS CloudHSM", "AWS CodeBuild", "AWS CodeCommit", "AWS CodeDeploy",
            "AWS CodePipeline", "AWS Code Signing for Amazon FreeRTOS",
            "AWS CodeStar", "AWS Cost and Usage Report",
            "AWS Cost Explorer Service", "AWS Database Migration Service (DMS)",
            "AWS Device Farm", "AWS Direct Connect", "AWS Directory Service",
            "AWS Elemental MediaConvert", "AWS Elemental MediaLive",
            "AWS Elemental MediaPackage", "AWS Elemental MediaStore",
            "AWS Firewall Manager", "AWS Greengrass",
            "AWS Import Export Disk Service", "AWS IoT", "AWS IoT 1-Click",
            "AWS Marketplace", "AWS Marketplace Management Portal",
            "AWS Marketplace Metering Service", "AWS Migration Hub",
            "AWS Mobile Hub", "AWS Organizations", "AWS Performance Insights",
            "AWS Price List", "AWS Security Token Service (STS)",
            "AWS Serverless Application Repository", "AWS Service Catalog",
            "AWS Shield", "Amazon Storage Gateway", "AWS Support",
            "AWS Trusted Advisor", "AWS XRay", "Auto Scaling", "Data Pipeline",
            "Single Sign-On (SSO)", "TensorFlow on AWS",
        ),
        considerations=(
            ("Amazon EC2", "On lab save, EC2 resources are suspended and "
             "billing pauses.  On resume, the EC2 instance reboots and then "
             "becomes available for use.  Plan lab step ordering around the "
             "reboot delay."),
            ("Amazon EC2 Container Service (ECS)", "On lab save, ECS task "
             "counts are automatically lowered to reduce resource consumption.  "
             "On resume, task counts are automatically increased again."),
            ("Amazon SNS", "If a learner creates an SNS subscription but does "
             "not verify it, the subscription stays in a pending state.  "
             "Pending subscriptions cannot be manually removed from the AWS "
             "account and may appear as residue in subsequent lab instances; "
             "AWS auto-removes them after 3 days."),
        ),
        setup_prerequisites=(
            "Dedicated AWS root account (not a sub-account, not a production account)",
            "AWS Organization enabled on the root account",
            "Billing configured",
            "IAM user with AWSOrganizationsFullAccess + AdministratorAccess",
            "Default 10-account quota — quota ticket required for larger events",
            "Permission Boundary (LabSecureAccess policy) applied to lab-created IAM users",
            "Protected resources — LabSecureAccess + Lab Developer policy removal is blocked for lab users automatically",
        ),
        modes=("Automated + Dedicated subscription pool",),
        related_capabilities=(
            "Cloud Security Review",
            "Cloud Credential Pool",
            "AWS Virtualization",
        ),
        last_updated="2024-09-24",
    ),

    # ─────────────────────────────────────────────────────────────────────
    # Cross-fabric capabilities
    # ─────────────────────────────────────────────────────────────────────

    SkillableCapability(
        name="Automated Scoring",
        fabric="cross",
        description=(
            "Labs include automated scoring and validation via multiple "
            "surfaces: product APIs, PowerShell, OS / cloud CLIs, Azure "
            "Resource Graph queries, and AI Vision on screen state.  Works "
            "across all fabrics — Datacenter VMs, Cloud Slice (Azure + AWS), "
            "and Simulations."
        ),
    ),

    SkillableCapability(
        name="BIOS GUID Pinning",
        fabric="cross",
        description=(
            "Skillable can pin a Custom UUID (BIOS GUID) in VM profiles.  "
            "Handles hardware-fingerprinted licensing where the product "
            "validates a specific motherboard UUID.  Applies to Datacenter VM "
            "fabrics."
        ),
    ),

    SkillableCapability(
        name="Cloud Credential Pool",
        fabric="cross",
        description=(
            "Pre-provisioned credential distribution for labs that need "
            "learners to log into a SaaS product, a web portal, a vendor "
            "dashboard, or any external platform.  NOT used for VM "
            "credentials (those come from the VM profile) or for Cloud "
            "Slice Azure/AWS subscription credentials (those come from the "
            "subscription pool and are auto-populated in instructions).  "
            "Credentials are uploaded in bulk, distributed via replacement "
            "tokens in lab instructions, and reused according to a "
            "configurable Reuse Policy (always-new, per-user/class, per-"
            "lab-profile, per-series, always-reuse-with-cooldown).  Supports "
            "custom credential properties beyond Username/Password, demo mode "
            "for rehearsal, low-availability alerting, and per-credential "
            "expiration.  Recycling honors a configured cooldown after labs "
            "move to OFF state so credentials are not reassigned while post-"
            "lab review is in progress.  This is the right access mechanism "
            "for products whose learner access model is 'SaaS login' or "
            "'external portal account'."
        ),
    ),

    SkillableCapability(
        name="Cloud Security Review",
        fabric="cross",
        description=(
            "Mandatory security review process for all Cloud Slice labs "
            "before external publication.  Applies to both Azure and AWS "
            "Cloud Slice.  Classifies labs as Low / Medium / High risk based "
            "on Access Control Policy restrictions, Life Cycle Action "
            "behavior, lab duration, and save-lab settings.  Primary threat "
            "model: cryptocurrency mining via unconstrained compute.  "
            "Approval conditions depend on consumption context — High-risk "
            "labs require expiration + acknowledgement + sometimes contract "
            "addendum; Medium-risk labs can ship with a paywall + unique "
            "accounts; Low-risk labs can ship free and public.  Pre-approved "
            "'Managed ACPs' bypass the review step entirely.  AWS free-tier "
            "allowances (t2.micro / t3.micro up to 750 hours per month) are "
            "explicit exceptions in the High-risk criteria."
        ),
        related_capabilities=("Cloud Slice - Azure", "Cloud Slice - AWS"),
    ),

    SkillableCapability(
        name="Hyper-V Preference",
        fabric="cross",
        description=(
            "Always prefer Skillable Datacenter (Hyper-V) over cloud VMs "
            "when the product does not specifically require cloud "
            "infrastructure.  Datacenter VMs launch predictably, have no idle "
            "storage costs, no egress charges, and no throttling.  Cloud "
            "fabrics are preferred only when the product IS the cloud "
            "(Azure-native, AWS-native) or the lab specifically teaches cloud "
            "operations."
        ),
        related_capabilities=("Skillable Datacenter",),
    ),

    SkillableCapability(
        name="M365 Tenant Provisioning",
        fabric="azure",
        description=(
            "Automated M365 tenant provisioning via Azure Cloud Slice — one "
            "dedicated tenant per learner.  Three tiers: Base (E3), Full "
            "(E5), Full+AI (E7 coming soon).  Two primary scenarios — "
            "end_user (learner consumes M365 apps) and administration "
            "(learner manages M365 admin surface).  Administration path has "
            "additional identity verification friction compared to the "
            "MOC/trial pattern, which the scorer treats as amber rather than "
            "green."
        ),
        related_capabilities=("Cloud Slice - Azure",),
    ),

    SkillableCapability(
        name="Skillable Simulations",
        fabric="simulation",
        description=(
            "For scenarios where real provisioning is impractical or "
            "economically unjustifiable — Skillable builds a deterministic "
            "simulation of the target product's UI and behavior.  AI Vision "
            "compute and platform overhead apply.  Scoring of automated "
            "tasks inside simulations is not supported today (feature "
            "request, not a current capability); this is the intentional "
            "Simulation Scoring = zero-credit rule in the Pillar 1 scorer."
        ),
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# Prompt-time renderers
#
# These produce canonical text blocks that get stitched into Claude prompts.
# Separating rendering from data means a capability-name rename or a new
# supported service flows through to the prompt on the next call without any
# prompt-file edits.
# ═══════════════════════════════════════════════════════════════════════════════

def get_capability(name: str) -> Optional[SkillableCapability]:
    """Look up a capability by exact name.  Returns None if not found."""
    for cap in SKILLABLE_CAPABILITIES:
        if cap.name == name:
            return cap
    return None


def render_capability_bullets_compact() -> str:
    """Short one-line summary of each capability — used in discovery prompts
    where the researcher only needs a high-level map of what Skillable can do."""
    lines = ["Skillable's core capabilities include:"]
    for cap in SKILLABLE_CAPABILITIES:
        # First sentence only, trim trailing period/space
        first_sentence = cap.description.split(".")[0].strip()
        lines.append(f"- {cap.name}: {first_sentence}.")
    return "\n".join(lines)


def render_aws_service_context() -> str:
    """Focused AWS Cloud Slice context — for the Pillar 1 labability fact
    extractor.  Emits the supported + unsupported service lists plus the
    three considerations so the extractor can flag unsupported-service
    dependencies with evidence."""
    cap = get_capability("Cloud Slice - AWS")
    if cap is None:
        return ""
    lines = [
        "═══ AWS CLOUD SLICE SUPPORT MATRIX ═══",
        "",
        "If the product being researched depends on AWS services, check the "
        "product's service dependencies against the lists below.  Unsupported "
        "services are AMBER, not red — Skillable can add support on demand, "
        "there has simply been no demand yet.  Surface the specific "
        "unsupported dependencies in the product's provisioning / access "
        "narrative so the scorer can reason about them.",
        "",
        "Supported AWS services (" + str(len(cap.supported_services)) + "):",
    ]
    # Render supported list in wrapped groups for token efficiency
    lines.append("  " + ", ".join(cap.supported_services))
    lines.append("")
    lines.append("NOT supported today (" + str(len(cap.unsupported_services)) + "):")
    lines.append("  " + ", ".join(cap.unsupported_services))
    lines.append("")
    lines.append("Special considerations:")
    for topic, note in cap.considerations:
        lines.append(f"  - {topic}: {note}")
    if cap.last_updated:
        lines.append("")
        lines.append(f"(AWS support matrix last updated: {cap.last_updated})")
    return "\n".join(lines)


def render_azure_service_context() -> str:
    """Focused Azure Cloud Slice context — for the Pillar 1 labability fact
    extractor.  Azure's answer is 'ALL services supported after security
    review', so this renders the orchestration nuance rather than a service
    list."""
    cap = get_capability("Cloud Slice - Azure")
    if cap is None:
        return ""
    lines = [
        "═══ AZURE CLOUD SLICE CONTEXT ═══",
        "",
        cap.description,
        "",
    ]
    if cap.modes:
        lines.append("Modes:")
        for mode in cap.modes:
            lines.append(f"  - {mode}")
        lines.append("")
    if cap.templates_supported:
        lines.append(
            "IaC paths: " + ", ".join(cap.templates_supported)
        )
        lines.append("")
    if cap.authoritative_catalog_url:
        lines.append(
            "Authoritative Azure service catalog: " + cap.authoritative_catalog_url
        )
    return "\n".join(lines)


def render_cross_fabric_context() -> str:
    """Capabilities that apply across fabrics — Credential Pool, Security
    Review, Automated Scoring, Hyper-V Preference.  Included so the
    researcher can pick the right access pattern for SaaS-login products
    and the scorer can grade access credibly."""
    lines = ["═══ CROSS-FABRIC SKILLABLE CAPABILITIES ═══", ""]
    cross_names = (
        "Cloud Credential Pool",
        "Cloud Security Review",
        "Automated Scoring",
        "Hyper-V Preference",
        "BIOS GUID Pinning",
        "M365 Tenant Provisioning",
        "Skillable Simulations",
    )
    for name in cross_names:
        cap = get_capability(name)
        if cap is None:
            continue
        lines.append(f"**{cap.name}**")
        lines.append(cap.description)
        lines.append("")
    return "\n".join(lines)


def render_full_capability_context() -> str:
    """Full capability context for the discovery prompt — compact bullets
    at the top, with the depth available if a grader / extractor wants
    it.  Kept to a sensible size — the per-pillar extractors get more
    focused sub-renders (render_aws_service_context, etc.)."""
    parts = [
        render_capability_bullets_compact(),
        "",
        render_azure_service_context(),
        "",
        render_aws_service_context(),
        "",
        render_cross_fabric_context(),
    ]
    return "\n".join(parts)


def render_capability_context_for_product(product: dict) -> str:
    """Scoped capability context for per-product Pillar 1 fact extraction.

    Full context (~11KB) is overkill for products that don't touch AWS or
    Azure.  Most products only need the compact bullets + cross-fabric
    capabilities (Credential Pool, Security Review, etc. — small, useful
    always).  AWS-specific products additionally get the supported /
    unsupported services list.  Azure-specific products additionally get
    the CSR/CSS + IaC context.

    Heuristic: inspect the product's discovery-level fields (name,
    description, category, deployment_model) for AWS / Azure hints.
    Lean toward INCLUDE when signals are mixed — the cost of a slightly
    larger prompt is much less than the cost of missing a SageMaker-class
    amber on a product that turns out to be AWS-dependent.
    """
    # Build a lowercased signal blob once.
    blob = " ".join(
        str(product.get(k, "") or "")
        for k in ("name", "description", "category", "subcategory",
                  "deployment_model", "orchestration_method")
    ).lower()

    include_aws = any(tok in blob for tok in (
        "aws", "amazon web services", "ec2", "s3 ", "lambda", "sagemaker",
        "dynamodb", "cloudformation", "amazon ",
    ))
    include_azure = any(tok in blob for tok in (
        "azure", "entra", "microsoft 365", "m365", "sharepoint",
        "power platform", "fabric", "dynamics 365", "bicep", "arm template",
    ))

    parts = [render_capability_bullets_compact(), ""]
    if include_azure:
        parts.extend([render_azure_service_context(), ""])
    if include_aws:
        parts.extend([render_aws_service_context(), ""])
    parts.append(render_cross_fabric_context())
    return "\n".join(parts)
