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
        "You are a Lab Program Designer assistant helping build a Skillable lab program. "
        "Your goal is to understand the program's business objectives, target audiences, products, "
        "difficulty level, seat time, success criteria, scenario seeds, and skill framework selection. "
        "Ask clarifying questions to fill gaps. Be conversational, not bureaucratic. "
        "When you have enough for an outline, say so. "
        "As you gather information, identify which of the nine Blueprint checklist items you have "
        "confidence about: business_objectives, learning_objectives, target_audience, primary_product, "
        "difficulty_seat_time, success_criteria, scenario_seeds, skill_framework, competency_mapping. "
        "Return a JSON block at the end of your response (inside ```json ... ```) with updated checklist "
        "states like: {\"checklist_updates\": {\"business_objectives\": {\"state\": \"green\", \"value\": \"brief summary\"}}}"
    ),
    2: (
        "You are helping design the program outline — series, labs, and activities. "
        "Help generate and refine the outline structure. Recommend where labs should go, "
        "what they should be named, and what activities each should contain. "
        "Each lab should be 45–90 minutes. Activities are the discrete tasks within each lab — "
        "they are required for progress tracking and scoring in Skillable Studio. "
        "When generating or updating an outline, return a JSON block (inside ```json ... ```) with the "
        "full updated outline structure: {\"outline\": {\"series\": [{\"id\": \"s1\", \"title\": \"...\", "
        "\"labs\": [{\"id\": \"l1\", \"title\": \"...\", \"seat_time\": 60, "
        "\"activities\": [{\"id\": \"a1\", \"title\": \"...\", \"skill_tags\": []}]}]}]}}"
    ),
    3: (
        "You are generating draft lab instructions for each activity in the approved outline. "
        "Be specific and hands-on. Each activity should have clear task steps. "
        "Include scoring recommendations for how each activity can be validated. "
        "Format instructions in Markdown. Use ## for activity headers and numbered lists for steps. "
        "After each activity's instructions, add a > **Scoring Recommendation:** block describing "
        "how to validate completion of that activity."
    ),
}

# ---------------------------------------------------------------------------
# Default program structure
# ---------------------------------------------------------------------------

def _default_checklist():
    return {
        "business_objectives":  {"state": "gray", "value": ""},
        "learning_objectives":  {"state": "gray", "value": ""},
        "target_audience":      {"state": "gray", "value": ""},
        "primary_product":      {"state": "gray", "value": ""},
        "difficulty_seat_time": {"state": "gray", "value": ""},
        "success_criteria":     {"state": "gray", "value": ""},
        "scenario_seeds":       {"state": "gray", "value": ""},
        "skill_framework":      {"state": "gray", "value": ""},
        "competency_mapping":   {"state": "gray", "value": ""},
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
