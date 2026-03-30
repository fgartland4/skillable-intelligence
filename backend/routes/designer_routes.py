"""Designer blueprint — lab program design wizard."""

import logging
import anthropic
from flask import Blueprint, render_template, request, jsonify
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Designer Blueprint
# ---------------------------------------------------------------------------

designer = Blueprint("designer", __name__, url_prefix="/designer")


@designer.route("/")
@designer.route("")
def designer_home():
    return render_template("designer.html")


@designer.route("/chat", methods=["POST"])
def designer_chat():
    """Proxy Claude API calls server-side — keeps the API key out of the browser."""
    body = request.get_json()
    if not body:
        return jsonify({"error": "JSON body required"}), 400

    messages = body.get("messages", [])
    max_tokens = int(body.get("max_tokens", 4096))

    system_msg = next((m["content"] for m in messages if m.get("role") == "system"), None)
    chat_messages = [{"role": m["role"], "content": m["content"]}
                     for m in messages if m.get("role") != "system"]

    if not chat_messages:
        return jsonify({"error": "No user/assistant messages provided"}), 400

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        kwargs = dict(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=chat_messages,
        )
        if system_msg:
            kwargs["system"] = system_msg

        response = client.messages.create(**kwargs)
        text = response.content[0].text if response.content else ""
        return jsonify({"text": text})
    except anthropic.RateLimitError:
        return jsonify({"error": "Rate limit reached — please wait a moment and try again."}), 429
    except anthropic.APIStatusError as e:
        if e.status_code == 400 and "credit balance" in str(e).lower():
            return jsonify({"error": "Anthropic API credits exhausted — contact your admin."}), 402
        log.exception("Designer chat API error")
        return jsonify({"error": f"API error ({e.status_code})"}), 502
    except Exception:
        log.exception("Designer chat failed")
        return jsonify({"error": "Server error — please try again."}), 500


