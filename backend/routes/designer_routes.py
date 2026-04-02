"""Designer blueprint — lab program design wizard."""

import json
import logging
import uuid
from datetime import datetime, timezone

import anthropic
from flask import Blueprint, Response, jsonify, redirect, render_template, request, stream_with_context, url_for

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from storage import (
    list_designer_programs,
    load_designer_program,
    save_designer_program,
)
from intelligence import generate_vocabulary, _BASE_LOADING_STATES

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Designer Blueprint
# ---------------------------------------------------------------------------

designer = Blueprint("designer", __name__, url_prefix="/designer")

# ---------------------------------------------------------------------------
# Phase-specific system prompts
# ---------------------------------------------------------------------------

PHASE_PROMPTS = {
    1: (
        "You are a sharp, experienced lab program designer at Skillable. "
        "You know instructional design cold and you know technology. "
        "Your job: make the person feel like they're in good hands, do your homework in the background, "
        "and move the program forward efficiently.\n\n"

        "VOICE & TONE — this is who you are:\n"
        "• Warm but not eager. Confident but not clinical. Like a trusted colleague who knows their stuff.\n"
        "• Never say 'Great question!' or 'Absolutely!' or perform enthusiasm. Just be present and useful.\n"
        "• When someone tells you what they're building, your first job is to make them feel heard — "
        "then signal you're doing background work — then invite them to keep going.\n"
        "• You don't interrogate. You gather.\n\n"

        "FIRST RESPONSE RULE — when the user first describes their program:\n"
        "• ONE sentence acknowledging what they're building.\n"
        "• ONE sentence saying you're pulling up research on the company or product "
        "('Give me a moment to look into [company/product]...').\n"
        "• ONE sentence inviting them to keep typing or uploading while you work.\n"
        "• Do NOT ask a clarifying question in this first response. Save it for the next turn.\n\n"

        "SUBSEQUENT TURNS — follow these rules on every turn after the first:\n"
        "• Maximum 3 sentences. Never more.\n"
        "• Ask exactly ONE question per turn. Never two.\n"
        "• No bullet points. No headers. No numbered lists. This is a conversation.\n"
        "• If you can infer something confidently, state it and ask them to confirm or correct.\n"
        "• When you have enough for a solid outline, say so in one sentence.\n\n"

        "You are filling four Lab Blueprint items through conversation: program_objectives, target_audience, "
        "primary_product, success_criteria. (difficulty_seat_time and skill_framework come from Preferences — "
        "do not ask about them.) Work through them naturally — never list or name them.\n\n"

        "INTELLIGENCE: You have deep knowledge of technology products, their ecosystems, typical audiences, "
        "and delivery patterns. Use it. Proactively name the likely product and audience based on what "
        "you know — don't wait for the user to spell it out. State your assumption, then confirm.\n\n"

        "When items become clear, append a JSON block at the END of your response (after your message):\n"
        "```json\n"
        "{\"checklist_updates\": {\"program_objectives\": {\"state\": \"yellow\", \"items\": [\"Support partner pre-sales enablement\"]}}}\n"
        "```\n"
        "Use state 'yellow' for partial, 'green' when confident. Always use 'items' (array), not 'value'. "
        "Merge incrementally — only include keys that changed. De-duplicate silently."
    ),
    2: (
        "You are Neo — a sharp, confident lab program designer at Skillable.\n\n"

        "RESPONSE RULES — follow these on every single turn:\n"
        "• Maximum 3 sentences in conversational replies. Never write walls of text.\n"
        "• Ask exactly ONE question per turn.\n"
        "• No bullet points, no headers, no numbered lists in chat text.\n"
        "• When generating or updating an outline, produce the JSON immediately — no preamble.\n\n"

        "You are designing the program outline: series, labs, and activities. "
        "Each lab is 45–90 minutes. Activities are discrete scored tasks within each lab.\n\n"

        "When generating or updating an outline, return a JSON block:\n"
        "```json\n"
        "{\"outline\": {\"series\": [{\"id\": \"s1\", \"title\": \"...\", "
        "\"labs\": [{\"id\": \"l1\", \"title\": \"...\", \"seat_time\": 60, "
        "\"activities\": [{\"id\": \"a1\", \"title\": \"...\", \"skill_tags\": []}]}]}]}}\n"
        "```"
    ),
    3: (
        "You are generating draft lab instructions for each activity in the approved outline. "
        "Be specific and hands-on. Each activity should have clear task steps. "
        "Include scoring recommendations for how each activity can be validated. "
        "Format instructions in Markdown. Use ## for activity headers and numbered lists for steps. "
        "After each activity's instructions, add a > **Scoring Recommendation:** block describing "
        "how to validate completion of that activity.\n\n"
        "CRITICAL — Program context will include style guides and skill frameworks. You MUST:\n"
        "• Follow every style guide listed — apply their voice, terminology, and formatting rules throughout.\n"
        "• If a custom style guide is provided, treat it as the primary writing authority.\n"
        "• Map each activity to the skill frameworks listed — include a brief skill tag or competency reference after each activity header.\n"
        "• If a custom skill framework is provided, use its taxonomy for mapping."
    ),
}

# ---------------------------------------------------------------------------
# Default program structure
# ---------------------------------------------------------------------------

def _default_checklist():
    # 6 items — Scenario Seeds removed (see project_tool_checklists.md for future re-add)
    return {
        "program_objectives":   {"state": "gray", "items": [], "value": ""},
        "target_audience":      {"state": "gray", "items": [], "value": ""},
        "primary_product":      {"state": "gray", "items": [], "value": ""},
        "difficulty_seat_time": {"state": "green", "items": [], "value": ""},
        "success_criteria":     {"state": "gray", "items": [], "value": ""},
        "skill_framework":      {"state": "gray", "items": [], "value": ""},
    }


def _default_program(program_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "program_id": program_id,
        "program_name": "New Program",
        "company_name": "",
        "current_phase": 1,
        "created_at": now,
        "updated_at": now,
        "checklist": _default_checklist(),
        "outline": {"series": []},
        "phase1_messages": [],
        "phase2_messages": [],
        "phase3_messages": [],
        "draft_instructions": {},
        "preferences": {
            "default_series_count": 3,
            "default_labs_per_series": 4,
            "default_seat_time": 60,
            "default_difficulty": "Intermediate",
            "skill_frameworks": [],
            "breakfix_default": False,
            "collaborative_lab_default": False,
            "simulated_attack_default": False,
            "brand_logo": "",
            "brand_url": "",
            "export_format": "ZIP",
            "sme_handoff_format": "docx",
        },
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@designer.route("/")
@designer.route("")
def designer_home():
    programs = list_designer_programs()
    return render_template("designer_home.html", programs=programs)


@designer.route("/new")
def new_program():
    program_id = str(uuid.uuid4())[:8]
    program = _default_program(program_id)
    save_designer_program(program_id, program)
    return redirect(url_for("designer.designer_app", program_id=program_id))


@designer.route("/<program_id>")
def designer_app(program_id: str):
    program = load_designer_program(program_id)
    if program is None:
        return redirect(url_for("designer.designer_home"))
    return render_template("designer.html", program=program, program_json=json.dumps(program))


@designer.route("/<program_id>/save", methods=["POST"])
def save_program(program_id: str):
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    existing = load_designer_program(program_id)
    if existing is None:
        return jsonify({"error": "Program not found"}), 404
    # Merge top-level keys from request into existing, preserving created_at
    for key, value in data.items():
        if key != "created_at":
            existing[key] = value
    save_designer_program(program_id, existing)
    return jsonify({"ok": True, "program_id": program_id})


@designer.route("/<program_id>/chat", methods=["POST"])
def designer_chat(program_id: str):
    """Phase-aware streaming AI chat (SSE)."""
    body = request.get_json()
    if not body:
        return jsonify({"error": "JSON body required"}), 400

    phase = int(body.get("phase", 1))
    messages = body.get("messages", [])
    context = body.get("context", "")

    system_prompt = PHASE_PROMPTS.get(phase, PHASE_PROMPTS[1])
    if context:
        system_prompt = system_prompt + "\n\nProgram context:\n" + context

    # Filter to user/assistant only
    chat_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m.get("role") in ("user", "assistant")
    ]
    if not chat_messages:
        return jsonify({"error": "No messages provided"}), 400

    def generate():
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            with client.messages.stream(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=chat_messages,
            ) as stream:
                for text in stream.text_stream:
                    # Escape newlines for SSE
                    payload = json.dumps({"text": text})
                    yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except anthropic.RateLimitError:
            yield f"data: {json.dumps({'error': 'Rate limit reached — please wait a moment.'})}\n\n"
        except anthropic.APIStatusError as e:
            if e.status_code == 400 and "credit balance" in str(e).lower():
                yield f"data: {json.dumps({'error': 'Anthropic API credits exhausted.'})}\n\n"
            else:
                log.exception("Designer chat API error")
                yield f"data: {json.dumps({'error': f'API error ({e.status_code})'})}\n\n"
        except Exception:
            log.exception("Designer chat failed")
            yield f"data: {json.dumps({'error': 'Server error — please try again.'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@designer.route("/<program_id>/checklist", methods=["GET"])
def get_checklist(program_id: str):
    program = load_designer_program(program_id)
    if program is None:
        return jsonify({"error": "Program not found"}), 404
    return jsonify(program.get("checklist", _default_checklist()))


@designer.route("/<program_id>/checklist", methods=["POST"])
def update_checklist(program_id: str):
    program = load_designer_program(program_id)
    if program is None:
        return jsonify({"error": "Program not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    checklist = program.get("checklist", _default_checklist())
    # data may be { item_key: { state, value } } or { updates: { ... } }
    updates = data.get("updates", data)
    for key, val in updates.items():
        if key in checklist:
            checklist[key] = val
    program["checklist"] = checklist
    save_designer_program(program_id, program)
    return jsonify({"ok": True, "checklist": checklist})


@designer.route("/<program_id>/vocabulary")
def get_vocabulary(program_id: str):
    """Return VocabularyPack loading_states for this program.

    If the program has a company_name set (from Inspector seed or manual entry),
    generates a full company-blended VocabularyPack and returns its loading_states.
    Otherwise returns just the base Skillable loading states.
    """
    program = load_designer_program(program_id)
    if program is None:
        return jsonify({"loading_states": _BASE_LOADING_STATES})
    company_name = program.get("company_name", "").strip()
    analysis_id = program.get("analysis_id")  # set when seeded from Inspector
    if not company_name:
        return jsonify({"loading_states": _BASE_LOADING_STATES})
    try:
        pack = generate_vocabulary(company_name, analysis_id=analysis_id)
        return jsonify({"loading_states": pack.get("loading_states", _BASE_LOADING_STATES)})
    except Exception as e:
        log.warning("get_vocabulary: failed for %s: %s", company_name, e)
        return jsonify({"loading_states": _BASE_LOADING_STATES})


@designer.route("/<program_id>/product-intel", methods=["POST"])
def product_intel(program_id: str):
    """Lightweight intelligence lookup for a product identified in Phase 1 conversation.

    Step 1: pure cache read (free, instant).
    Step 2: if not found and company_name provided, run qualify() — discover + light scoring.
    Returns { found, summary, score_boost }.
    """
    program = load_designer_program(program_id)
    if program is None:
        return jsonify({"error": "Program not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    product_name = (data.get("product_name") or "").strip()
    company_name = (data.get("company_name") or "").strip()

    if not product_name and not company_name:
        return jsonify({"found": False, "summary": "", "score_boost": 0}), 200

    from intelligence import lookup, qualify
    from storage import find_analysis_by_company_name, find_discovery_by_company_name

    # Step 1 — cache read (no API cost)
    lookup_name = company_name or product_name
    cached = lookup(lookup_name)
    if cached.get("found"):
        analysis = cached.get("analysis") or {}
        products = analysis.get("products_json") or []
        matched = next(
            (p for p in products
             if product_name and product_name.lower() in (p.get("name", "")).lower()),
            None,
        )
        if matched:
            delivery = matched.get("recommended_delivery_pattern", "")
            lab_score = matched.get("lab_score", 0)
            summary = (
                f"delivery via {delivery}, labability score {lab_score}"
                if delivery else f"labability score {lab_score}"
            )
            return jsonify({"found": True, "summary": summary, "score_boost": 20})
        # Company found in cache but specific product not matched — still useful signal
        co = analysis.get("company_name") or company_name
        return jsonify({"found": True, "summary": f"{co} analysis loaded from Inspector", "score_boost": 10})

    # Step 2 — qualify (discover + light Claude scoring) — only if we have a company name
    if company_name:
        try:
            row = qualify(company_name)
            if row:
                method = row.get("labability_method") or ""
                summary = f"discovered via Intelligence — {method}" if method else "discovered via Intelligence"
                return jsonify({"found": True, "summary": summary, "score_boost": 15})
        except Exception:
            log.warning("product_intel: qualify failed for %s / %s", company_name, product_name)

    return jsonify({"found": False, "summary": "", "score_boost": 0}), 200


@designer.route("/<program_id>/outline", methods=["POST"])
def save_outline(program_id: str):
    program = load_designer_program(program_id)
    if program is None:
        return jsonify({"error": "Program not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    program["outline"] = data.get("outline", program.get("outline", {"series": []}))
    save_designer_program(program_id, program)
    return jsonify({"ok": True})
