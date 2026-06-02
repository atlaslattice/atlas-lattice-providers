#!/usr/bin/env python3
"""
GoogleProvider — Production Multi-Cloud Implementation (v3.0)
=============================================================
Implements the GoogleProvider class, demonstrating standard Google API service
initialization using the inherited OAuth 2.0 token from the multi-cloud bridge
(CopilotCLIBridge mapping Azure sessions to GOOGLE_EXTERNAL_OAUTH_TOKEN).

Fully implements ProviderContract.
Uses standardized error taxonomy (provider_errors.make_error).
Uses observability (record_event + _timed_operation) consistent with v1.2+ providers.
Consumes GOOGLE_EXTERNAL_OAUTH_TOKEN when the bridge has prepared the cross-cloud handoff.
Graceful fallback to local token.json.
Normalized return shapes for search/fetch/etc. compatible with NotionProvider / MicrosoftProvider.

See also: agent_ms_cli_bridge.py for the token mapping logic.
"""

import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional

# Setup logging to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("provider_google")

# --- Optional Google imports with graceful fallback ---
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Missing Google API libraries. Please run: pip install google-api-python-client google-auth")
    # Stub classes for local compilation checks
    class Credentials: pass
    def build(*args, **kwargs): pass
    class HttpError(Exception): pass

# Gemini (Generative AI) support - using the modern google-genai package
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed. Run: pip install google-genai to enable Gemini AI features.")

from provider_contract import ProviderContract
from provider_errors import ProviderErrorCode, make_error

# Cross-cloud bridge for token inheritance (MS <-> Google)
try:
    from agent_ms_cli_bridge import CopilotCLIBridge
except Exception:
    CopilotCLIBridge = None


class GoogleProvider(ProviderContract):
    """Provides standard, grounded interfaces for Google Workspace / Drive operations."""

    def __init__(self, token_path: str = "config/token.json", bridge: Any = None):
        self._name = "google"
        self.token_path = token_path
        self.service = None
        self.bridge = bridge or (CopilotCLIBridge() if CopilotCLIBridge else None)
        self.gemini_model = None
        self._initialize_service()
        self._initialize_gemini()  # separate from Drive OAuth; uses GOOGLE_API_KEY

    @property
    def name(self) -> str:
        return self._name

    # ============================================================
    # SERVICE INITIALIZATION (Bridge-aware + fallback)
    # ============================================================
    def _initialize_service(self):
        """
        Dynamically initializes the Google Drive API client using:
        1. The inherited multi-cloud environment token (GOOGLE_EXTERNAL_OAUTH_TOKEN) prepared by CopilotCLIBridge (preferred)
        2. A local saved user credentials token (token.json)
        3. Full standard OAuth flow using config/client_secrets.json (maximizes Google interop; see setup_environment.py)
        """
        if not GOOGLE_AVAILABLE:
            logger.warning("Google client libraries not available. Provider will run in degraded/stub mode.")
            return

        creds = None

        # Option 1: Inherit token from the multi-cloud environment (preferred, from bridge)
        env_token = os.getenv("GOOGLE_EXTERNAL_OAUTH_TOKEN")
        if env_token:
            logger.info("Initializing Google Drive client using inherited environment token (from CopilotCLIBridge / Azure handoff)...")
            try:
                # Use standard Google credentials constructor for Bearer tokens
                creds = Credentials(token=env_token)
            except Exception as e:
                logger.error(f"Failed to load credentials from environment token: {e}")

        # Option 2: Fallback to local saved credentials file
        if not creds and os.path.exists(self.token_path):
            logger.info(f"Fallback: Loading credentials from local file '{self.token_path}'...")
            try:
                creds = Credentials.from_authorized_user_file(self.token_path)
            except Exception as e:
                logger.warning(f"Failed to load local token file: {e}")

        # Option 3: Full OAuth flow using client_secrets.json (standard Google interop per Gemini/setup script)
        # Allows first-time auth or service accounts. Creates token.json for reuse.
        client_secrets_path = "config/client_secrets.json"
        if not creds and os.path.exists(client_secrets_path):
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                logger.info(f"Attempting standard OAuth flow using {client_secrets_path} for full Google Drive interop...")
                scopes = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.file']
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
                # For dev: local server. For prod/headless: use run_console() or service account.
                creds = flow.run_local_server(port=0)
                # Persist token for future runs (matches token_path)
                with open(self.token_path, 'w') as token_file:
                    token_file.write(creds.to_json())
                logger.info(f"OAuth successful. Token saved to {self.token_path} for reuse.")
            except Exception as e:
                logger.error(f"Failed OAuth flow with client_secrets.json: {e}")

        if creds:
            try:
                self.service = build('drive', 'v3', credentials=creds)
                logger.info("Google Drive service client built successfully.")
            except Exception as e:
                logger.error(f"Failed to build Google Drive service: {e}")
        else:
            logger.warning("No valid credentials found. Google Drive service remains uninitialized (stub mode). Run 'python setup_environment.py' or set tokens.")

    def _initialize_gemini(self, api_key: Optional[str] = None):
        """Initialize Gemini using the modern google-genai SDK.
        Prefers GOOGLE_API_KEY env var. The user's key has been integrated via environment.
        Uses a currently supported model (gemini-2.5-flash etc.).
        """
        if not GENAI_AVAILABLE:
            return
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            logger.warning("GOOGLE_API_KEY not set. Gemini AI features disabled. Set $env:GOOGLE_API_KEY=yourkey")
            return
        try:
            self.gemini_client = genai.Client(api_key=key)
            # Pick a reliable current model from the list returned by the user's key
            self.gemini_model_name = "gemini-2.5-flash"
            logger.info(f"Gemini client initialized with model {self.gemini_model_name}.")
        except Exception as e:
            logger.error(f"Failed to initialize modern Gemini client: {e}")
            self.gemini_client = None

    # ============================================================
    # OBSERVABILITY (v1.2+ requirement, matches other providers)
    # ============================================================
    async def record_event(self, kind: str, meta: Dict[str, Any]) -> None:
        """Observability hook. Emits to telemetry / logs. Standardized keys recommended."""
        from provider_telemetry import default_telemetry
        meta = dict(meta) if meta else {}
        meta.setdefault("provider", self.name)
        await default_telemetry.record_event(self.name, kind, meta)

    async def _timed_operation(self, operation_name: str, coro, meta: Optional[Dict[str, Any]] = None):
        """Helper for timing + auto record_event (start/success/error)."""
        meta = meta or {}
        start = time.perf_counter()
        await self.record_event("operation_start", {"operation": operation_name, **meta})

        try:
            result = await coro
            latency = round((time.perf_counter() - start) * 1000, 2)
            await self.record_event("operation_success", {
                "operation": operation_name,
                "latency_ms": latency,
                **meta
            })
            return result
        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            await self.record_event("operation_error", {
                "operation": operation_name,
                "latency_ms": latency,
                "error": str(e),
                **meta
            })
            raise

    # ============================================================
    # CORE PROVIDER CONTRACT METHODS (full implementation)
    # ============================================================
    async def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Search Google Drive files (standard API + bridge token support)."""
        if not self.service:
            return make_error(
                ProviderErrorCode.PROVIDER_DOWN,
                "Google Drive service not initialized (missing credentials or libraries)",
                self.name
            )

        async def _do_search():
            # Standard Google Drive API query syntax
            q = f"name contains '{query}'"
            logger.info(f"Executing standard Drive search query: \"{q}\"")

            try:
                results = self.service.files().list(
                    q=q,
                    pageSize=limit,
                    fields="files(id, name, mimeType, webViewLink, modifiedTime)"
                ).execute()

                files = results.get('files', [])
                return {
                    "status": "SUCCESS",
                    "provider": self.name,
                    "query": query,
                    "results": files,
                    "count": len(files)
                }
            except HttpError as e:
                if e.resp.status == 429:
                    return make_error(ProviderErrorCode.RATE_LIMIT, str(e), self.name)
                return make_error(ProviderErrorCode.PROVIDER_DOWN, str(e), self.name)
            except Exception as e:
                return make_error(ProviderErrorCode.INTERNAL_ERROR, str(e), self.name)

        return await self._timed_operation("search", _do_search(), {"query": query})

    async def fetch(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        """Fetch metadata + (optionally) content for a specific Drive file."""
        if not self.service:
            return make_error(ProviderErrorCode.PROVIDER_DOWN, "Google service not initialized", self.name)

        async def _do_fetch():
            try:
                file_meta = self.service.files().get(
                    fileId=resource_id,
                    fields="id, name, mimeType, webViewLink, modifiedTime, size, parents"
                ).execute()

                # For text files / Google Docs, one could export content here
                # (left as future enhancement; current returns metadata + note)
                content = None
                if file_meta.get("mimeType", "").startswith("text/"):
                    try:
                        content = self.service.files().get_media(fileId=resource_id).execute()
                        if isinstance(content, bytes):
                            content = content.decode("utf-8", errors="replace")
                    except Exception:
                        content = "<binary or export not supported in this call>"

                return {
                    "status": "SUCCESS",
                    "provider": self.name,
                    "resource_id": resource_id,
                    "metadata": file_meta,
                    "content": content
                }
            except HttpError as e:
                if e.resp.status == 404:
                    return make_error(ProviderErrorCode.NOT_FOUND, f"File not found: {resource_id}", self.name)
                return make_error(ProviderErrorCode.PROVIDER_DOWN, str(e), self.name)
            except Exception as e:
                return make_error(ProviderErrorCode.INTERNAL_ERROR, str(e), self.name)

        return await self._timed_operation("fetch", _do_fetch(), {"resource_id": resource_id})

    async def extract_claims(
        self,
        content: str,
        source_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Extract high-quality ClaimPackets using Gemini when available.
        Falls back to basic extraction if no model.
        """
        if not content:
            return []

        if GENAI_AVAILABLE and hasattr(self, 'gemini_client') and self.gemini_client:
            try:
                prompt = f"""You are a precise, sovereign claim extraction engine for a knowledge lattice.
Extract a list of high-signal, atomic, verifiable claims from the content.
For each claim produce:
- claim_text (concise, standalone)
- epistemic_class: one of "fact", "opinion", "hypothesis", "definition", "procedure"
- tags: array of short keywords
- confidence: float 0-1

Return ONLY valid JSON with top-level key "claims" containing the array.
Do not add any other text.

Content to process:
{content[:12000]}
"""
                model_name = getattr(self, 'gemini_model_name', 'gemini-2.5-flash')
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                text = getattr(response, "text", str(response)).strip()

                # Robust JSON extraction
                import json, re
                if "```json" in text:
                    text = text.split("```json", 1)[1].split("```", 1)[0]
                elif "```" in text:
                    text = text.split("```", 1)[1].split("```", 1)[0]

                text = re.sub(r'^[^{[]*', '', text)
                text = re.sub(r'[^}\]]*$', '', text)

                data = json.loads(text)
                claims = data.get("claims", []) if isinstance(data, dict) else data

                for c in claims:
                    if isinstance(c, dict):
                        c.setdefault("source", {})
                        c["source"]["provider"] = self.name
                        c["source"].update(source_metadata or {})
                        c.setdefault("epistemic_class", "fact")
                        c.setdefault("tags", ["google", "gemini"])
                        c.setdefault("confidence", 0.8)

                await self.record_event("extract_claims", {"count": len(claims), "model": model_name})
                return claims
            except Exception as e:
                logger.warning(f"Gemini claim extraction failed, falling back: {e}")

        # Basic fallback
        claims = [{
            "claim_text": content[:700],
            "epistemic_class": "raw",
            "tags": ["google", "drive", "fallback"],
            "source": {"provider": self.name, **(source_metadata or {})},
            "confidence": 0.5
        }]
        await self.record_event("extract_claims", {"count": len(claims), "fallback": True})
        return claims

    async def mirror(
        self,
        claim: Dict[str, Any],
        parent: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mirror a ClaimPacket back into Google Drive (stub — implement with Drive create)."""
        await self.record_event("mirror", {"claim_id": claim.get("id") or claim.get("claim_id"), "parent": parent})
        return {
            "provider": self.name,
            "status": "STUB",
            "mirrored_to": parent or "default_drive_folder",
            "claim_id": claim.get("claim_id") or claim.get("id"),
            "note": "Implement with google-api-python-client Drive files.create + permissions for full mirror."
        }

    async def execute(self, command: str, args: List[str], **kwargs) -> Dict[str, Any]:
        """GoogleProvider does not execute local CLI. Route to LocalCLIProvider."""
        return make_error(
            ProviderErrorCode.UNSUPPORTED_OPERATION,
            "execute() not supported on GoogleProvider. Use LocalCLIProvider for CLI tools.",
            self.name
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "supports": ["search", "fetch", "extract_claims", "mirror", "record_event"],
            "priority": 3,
            "description": "Google Drive / Workspace provider. Consumes GOOGLE_EXTERNAL_OAUTH_TOKEN from CopilotCLIBridge when available. Strong for grounded research and generative tasks.",
            "notes": "Requires google-api-python-client + google-auth. Token inheritance via agent_ms_cli_bridge."
        }

    async def health(self) -> Dict[str, Any]:
        status = "healthy" if self.service else "degraded"
        return {"status": status, "provider": self.name, "service_initialized": bool(self.service)}

    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """General purpose generation using the modern Gemini client.
        Used by higher-level engines for reasoning, extraction, summarization, etc.
        """
        if not GENAI_AVAILABLE or not hasattr(self, 'gemini_client') or not self.gemini_client:
            return make_error(
                ProviderErrorCode.PROVIDER_DOWN,
                "Gemini client not initialized (set GOOGLE_API_KEY and pip install google-genai)",
                self.name
            )

        model_name = model or getattr(self, 'gemini_model_name', 'gemini-2.5-flash')

        async def _do_generate():
            models_to_try = [model_name, "gemini-2.0-flash", "gemini-flash-latest", "gemini-pro-latest"]
            last_err = None
            for m in models_to_try:
                try:
                    response = self.gemini_client.models.generate_content(model=m, contents=prompt)
                    text = getattr(response, "text", str(response))
                    await self.record_event("generate", {"prompt_len": len(prompt), "model": m})
                    return {
                        "status": "SUCCESS",
                        "provider": self.name,
                        "text": text,
                        "model": m
                    }
                except Exception as e:
                    last_err = e
                    if "high demand" in str(e).lower() or "503" in str(e):
                        continue
                    break
            return make_error(ProviderErrorCode.INTERNAL_ERROR, str(last_err), self.name)

        return await self._timed_operation("generate", _do_generate(), {"prompt_len": len(prompt)})


if __name__ == "__main__":
    # Local developer verification block
    # Set your key before running:  $env:GOOGLE_API_KEY="your-key-here"
    # The user's key was integrated into the runtime environment for this session.

    provider = GoogleProvider()
    print("Capabilities:", provider.capabilities())

    import asyncio, os
    async def test_gemini():
        if not os.getenv("GOOGLE_API_KEY"):
            print("Set GOOGLE_API_KEY env var to test live Gemini calls.")
            return
        gen = await provider.generate('Confirm Gemini API integration in the GoogleProvider for Maximum Grok.')
        print('Generate status:', gen.get('status') if isinstance(gen, dict) else 'N/A')
        claims = await provider.extract_claims('The provider now uses the integrated Gemini key for high-quality extraction.')
        print('Extract count:', len(claims))

    asyncio.run(test_gemini())
