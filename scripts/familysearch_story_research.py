from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "familysearch.local.json"
DEFAULT_TOKEN_PATH = PROJECT_ROOT / "secrets" / "familysearch-token.json"
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "research" / "familysearch" / "exports"


DEFAULT_CONFIG = {
    "familysearch": {
        "app_key": "replace-with-your-familysearch-app-key",
        "environment": "beta",
        "redirect_uri": "http://127.0.0.1:8788/callback",
        "auth_base": "https://ident.familysearch.org/cis-web/oauth2/v3",
        "api_base": "https://apibeta.familysearch.org/platform",
        "scope": "openid profile email country",
    },
    "notes": "Local-only FamilySearch OAuth config. Do not commit.",
}


class FamilySearchError(RuntimeError):
    pass


class OAuthFlowError(RuntimeError):
    pass


@dataclass
class FamilySearchConfig:
    app_key: str
    environment: str
    redirect_uri: str
    auth_base: str
    api_base: str
    scope: str


class _CallbackHandler(BaseHTTPRequestHandler):
    server_version = "AncestorBooksFamilySearchOAuth/0.1"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        self.server.oauth_query = query  # type: ignore[attr-defined]
        if "error" in query:
            body = "FamilySearch OAuth was denied. You can close this tab."
        else:
            body = "FamilySearch OAuth succeeded. You can close this tab and return to Codex."
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:
        return


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> FamilySearchConfig:
    if not path.exists():
        raise FamilySearchError(f"Config file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    block = payload.get("familysearch", {})
    app_key = block.get("app_key", "").strip()
    if not app_key or app_key == "replace-with-your-familysearch-app-key":
        raise FamilySearchError(f"Missing familysearch.app_key in {path}")
    return FamilySearchConfig(
        app_key=app_key,
        environment=block.get("environment", "beta").strip() or "beta",
        redirect_uri=block.get("redirect_uri", DEFAULT_CONFIG["familysearch"]["redirect_uri"]).strip(),
        auth_base=block.get("auth_base", DEFAULT_CONFIG["familysearch"]["auth_base"]).strip(),
        api_base=block.get("api_base", DEFAULT_CONFIG["familysearch"]["api_base"]).strip(),
        scope=block.get("scope", DEFAULT_CONFIG["familysearch"]["scope"]).strip(),
    )


def write_default_config(path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")


def load_token(path: Path = DEFAULT_TOKEN_PATH) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_token(payload: dict, path: Path = DEFAULT_TOKEN_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode("ascii").rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).decode("ascii").rstrip("=")
    return verifier, challenge


def build_authorize_url(config: FamilySearchConfig, *, state: str, code_challenge: str) -> str:
    params = {
        "response_type": "code",
        "client_id": config.app_key,
        "redirect_uri": config.redirect_uri,
        "scope": config.scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{config.auth_base}/authorization?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(config: FamilySearchConfig, *, code: str, code_verifier: str) -> dict:
    payload = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": config.app_key,
            "redirect_uri": config.redirect_uri,
            "code_verifier": code_verifier,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{config.auth_base}/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        token_payload = json.loads(response.read().decode("utf-8"))
    token_payload["created_at"] = int(time.time())
    return token_payload


def run_local_oauth_flow(config: FamilySearchConfig, *, timeout_seconds: int = 240) -> tuple[str, dict]:
    redirect = urllib.parse.urlparse(config.redirect_uri)
    host = redirect.hostname or "127.0.0.1"
    port = redirect.port or 8788
    state = secrets.token_urlsafe(24)
    code_verifier, code_challenge = _pkce_pair()
    authorize_url = build_authorize_url(config, state=state, code_challenge=code_challenge)

    httpd = HTTPServer((host, port), _CallbackHandler)
    httpd.oauth_query = None  # type: ignore[attr-defined]
    server_thread = threading.Thread(target=httpd.handle_request, daemon=True)
    server_thread.start()

    print(f"Open this URL in your browser:\n{authorize_url}\n")
    server_thread.join(timeout_seconds)
    try:
        query = httpd.oauth_query  # type: ignore[attr-defined]
    finally:
        httpd.server_close()

    if not query:
        raise OAuthFlowError("Timed out waiting for FamilySearch OAuth callback")
    if query.get("state", [""])[0] != state:
        raise OAuthFlowError("OAuth state mismatch")
    if "error" in query:
        raise OAuthFlowError(f"OAuth denied: {query['error'][0]}")
    code = query.get("code", [""])[0]
    if not code:
        raise OAuthFlowError("OAuth callback did not include a code")
    token_payload = exchange_code_for_token(config, code=code, code_verifier=code_verifier)
    return authorize_url, token_payload


def access_token(config: FamilySearchConfig, token_path: Path = DEFAULT_TOKEN_PATH) -> str:
    payload = load_token(token_path)
    if not payload:
        raise FamilySearchError(f"No token file found at {token_path}")
    token = payload.get("access_token", "").strip()
    if not token:
        raise FamilySearchError(f"Token file at {token_path} does not contain an access_token")
    return token


def api_request_json(
    config: FamilySearchConfig,
    *,
    path: str,
    accept: str = "application/x-gedcomx-v1+json",
    params: dict[str, str] | None = None,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> dict:
    token = access_token(config, token_path)
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params)
    url = f"{config.api_base}{path}{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FamilySearchError(f"FamilySearch API error {exc.code}: {detail}") from exc


def current_user(config: FamilySearchConfig, *, token_path: Path = DEFAULT_TOKEN_PATH) -> dict:
    return api_request_json(config, path="/users/current", accept="application/x-fs-v1+json", token_path=token_path)


def current_person_id(config: FamilySearchConfig, *, token_path: Path = DEFAULT_TOKEN_PATH) -> str:
    payload = current_user(config, token_path=token_path)
    users = payload.get("users", [])
    if not users:
        raise FamilySearchError("Current user response did not include a user record")
    person_id = (users[0].get("personId") or "").strip()
    if not person_id:
        raise FamilySearchError("Current user does not appear to be linked to a tree person")
    return person_id


def read_person(config: FamilySearchConfig, person_id: str, *, token_path: Path = DEFAULT_TOKEN_PATH) -> dict:
    return api_request_json(config, path=f"/tree/persons/{person_id}", token_path=token_path)


def read_ancestry(config: FamilySearchConfig, person_id: str, generations: int, *, token_path: Path = DEFAULT_TOKEN_PATH) -> dict:
    return api_request_json(
        config,
        path=f"/tree/ancestry",
        params={"person": person_id, "generations": str(generations)},
        token_path=token_path,
    )


def read_sources(config: FamilySearchConfig, person_id: str, *, token_path: Path = DEFAULT_TOKEN_PATH) -> dict:
    return api_request_json(config, path=f"/tree/persons/{person_id}/sources", token_path=token_path)


def read_memories(config: FamilySearchConfig, person_id: str, *, token_path: Path = DEFAULT_TOKEN_PATH) -> dict:
    return api_request_json(config, path=f"/tree/persons/{person_id}/memories", token_path=token_path)


def read_notes(config: FamilySearchConfig, person_id: str, *, token_path: Path = DEFAULT_TOKEN_PATH) -> dict:
    return api_request_json(config, path=f"/tree/persons/{person_id}/notes", token_path=token_path)


def person_display_name(payload: dict) -> str:
    persons = payload.get("persons", [])
    if not persons:
        return ""
    display = persons[0].get("display", {})
    return display.get("name") or persons[0].get("id") or ""


def print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def write_story_dossier(
    config: FamilySearchConfig,
    *,
    person_id: str,
    generations: int,
    output_root: Path = DEFAULT_EXPORT_ROOT,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> None:
    person_payload = read_person(config, person_id, token_path=token_path)
    ancestry_payload = read_ancestry(config, person_id, generations, token_path=token_path)
    notes_payload = read_notes(config, person_id, token_path=token_path)
    sources_payload = read_sources(config, person_id, token_path=token_path)
    memories_payload = read_memories(config, person_id, token_path=token_path)

    name = person_display_name(person_payload) or person_id
    person_root = output_root / person_id
    person_root.mkdir(parents=True, exist_ok=True)

    (person_root / "person.json").write_text(json.dumps(person_payload, indent=2) + "\n", encoding="utf-8")
    (person_root / "ancestry.json").write_text(json.dumps(ancestry_payload, indent=2) + "\n", encoding="utf-8")
    (person_root / "notes.json").write_text(json.dumps(notes_payload, indent=2) + "\n", encoding="utf-8")
    (person_root / "sources.json").write_text(json.dumps(sources_payload, indent=2) + "\n", encoding="utf-8")
    (person_root / "memories.json").write_text(json.dumps(memories_payload, indent=2) + "\n", encoding="utf-8")

    source_descriptions = sources_payload.get("sourceDescriptions", [])
    notes = notes_payload.get("notes", [])
    memories = memories_payload.get("sourceDescriptions", [])
    persons = ancestry_payload.get("persons", [])

    markdown = [
        f"# FamilySearch Story Dossier: {name}",
        "",
        f"- Person ID: `{person_id}`",
        f"- Generations pulled: `{generations}`",
        f"- Ancestry persons returned: `{len(persons)}`",
        f"- Notes returned: `{len(notes)}`",
        f"- Source descriptions returned: `{len(source_descriptions)}`",
        f"- Memory descriptions returned: `{len(memories)}`",
        "",
        "## Suggested Research Path",
        "",
        "1. Read `person.json` to confirm this is the right ancestor and capture the canonical name and life dates.",
        "2. Read `ancestry.json` to place the ancestor in a branch and identify nearby story candidates.",
        "3. Read `notes.json` for authored summaries or family-written narrative fragments.",
        "4. Read `sources.json` for journals, autobiographies, or linked source artifacts.",
        "5. Read `memories.json` for stories, photos, and uploaded documents that may contain text worth adapting.",
        "",
        "## Raw Files",
        "",
        "- `person.json`",
        "- `ancestry.json`",
        "- `notes.json`",
        "- `sources.json`",
        "- `memories.json`",
    ]

    if source_descriptions:
        markdown.extend(["", "## Source Titles"])
        for item in source_descriptions[:15]:
            title = item.get("titles", [{}])[0].get("value", "").strip()
            about = item.get("about", "").strip()
            if title or about:
                markdown.append(f"- {title or about}")

    if notes:
        markdown.extend(["", "## Note Previews"])
        for item in notes[:10]:
            subject = item.get("subject", "").strip()
            text = item.get("text", "").strip().replace("\n", " ")
            preview = text[:200] + ("..." if len(text) > 200 else "")
            markdown.append(f"- {subject or 'Untitled note'}: {preview}")

    (person_root / "README.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(f"Wrote FamilySearch dossier to {person_root}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="familysearch-story-research",
        description="Local FamilySearch research helper for Ancestor Books",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-config", help="Write a local FamilySearch config template")
    init_parser.add_argument("--path", type=Path, default=DEFAULT_CONFIG_PATH)

    status_parser = subparsers.add_parser("oauth-status", help="Show local FamilySearch OAuth status")
    status_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    status_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    authorize_parser = subparsers.add_parser("oauth-authorize", help="Run a local FamilySearch OAuth flow")
    authorize_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    authorize_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    current_user_parser = subparsers.add_parser("current-user", help="Read the current FamilySearch user")
    current_user_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    current_user_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    current_person_parser = subparsers.add_parser("current-person", help="Read the current user's tree person")
    current_person_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    current_person_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    person_parser = subparsers.add_parser("person", help="Read a FamilySearch person")
    person_parser.add_argument("--person-id", required=True)
    person_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    person_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    ancestry_parser = subparsers.add_parser("ancestry", help="Read ancestry for a person")
    ancestry_parser.add_argument("--person-id", required=True)
    ancestry_parser.add_argument("--generations", type=int, default=4)
    ancestry_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    ancestry_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    sources_parser = subparsers.add_parser("sources", help="Read source references for a person")
    sources_parser.add_argument("--person-id", required=True)
    sources_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    sources_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    memories_parser = subparsers.add_parser("memories", help="Read memories for a person")
    memories_parser.add_argument("--person-id", required=True)
    memories_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    memories_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    notes_parser = subparsers.add_parser("notes", help="Read notes for a person")
    notes_parser.add_argument("--person-id", required=True)
    notes_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    notes_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)

    dossier_parser = subparsers.add_parser("story-dossier", help="Export a local FamilySearch research dossier for a person")
    dossier_parser.add_argument("--person-id", help="Explicit person id. If omitted, uses the current user's tree person")
    dossier_parser.add_argument("--generations", type=int, default=4)
    dossier_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    dossier_parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN_PATH)
    dossier_parser.add_argument("--output-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-config":
        write_default_config(args.path)
        print(f"Wrote FamilySearch config template to {args.path}")
        return

    config = load_config(args.config)

    if args.command == "oauth-status":
        token_payload = load_token(args.token)
        print(f"Config: present ({args.config})")
        print(f"Environment: {config.environment}")
        print(f"API base: {config.api_base}")
        print(f"Redirect URI: {config.redirect_uri}")
        print(f"Token file: {'present' if token_payload else 'missing'} ({args.token})")
        return

    if args.command == "oauth-authorize":
        _, token_payload = run_local_oauth_flow(config)
        write_token(token_payload, args.token)
        print("FamilySearch OAuth succeeded")
        print(f"Stored token at {args.token}")
        return

    if args.command == "current-user":
        print_json(current_user(config, token_path=args.token))
        return
    if args.command == "current-person":
        person_id = current_person_id(config, token_path=args.token)
        print_json(read_person(config, person_id, token_path=args.token))
        return
    if args.command == "person":
        print_json(read_person(config, args.person_id, token_path=args.token))
        return
    if args.command == "ancestry":
        print_json(read_ancestry(config, args.person_id, args.generations, token_path=args.token))
        return
    if args.command == "sources":
        print_json(read_sources(config, args.person_id, token_path=args.token))
        return
    if args.command == "memories":
        print_json(read_memories(config, args.person_id, token_path=args.token))
        return
    if args.command == "notes":
        print_json(read_notes(config, args.person_id, token_path=args.token))
        return
    if args.command == "story-dossier":
        person_id = args.person_id or current_person_id(config, token_path=args.token)
        write_story_dossier(
            config,
            person_id=person_id,
            generations=args.generations,
            output_root=args.output_root,
            token_path=args.token,
        )
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
