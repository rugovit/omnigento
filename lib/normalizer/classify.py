"""Classifier runtime boundary and output validation."""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import asdict

from .artifacts import REPO_ROOT, load_inventory, safe_artifact_name, update_manifest, utc_now, write_json
from .inventory import read_text_for_markers
from .models import ClassificationResult, ClassificationTask, DiscardedRule, ExtractedRule, InventoryRecord


MAX_CLASSIFIER_SOURCE_CHARS = 120_000

ALLOWED_STATUSES = {"classified", "not_classified", "error"}
ALLOWED_SCOPES = {
    "file-scoped",
    "topic-based",
    "on-request",
    "root-only",
    "discard",
}
ALLOWED_KINDS = {"safety", "workflow", "style", "command", "commands", "architecture", "config", "provider"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def classification_output_contract() -> dict[str, object]:
    return {
        "source_path": "string; must match task.source_path",
        "surface_id": "string; must match task.surface_id",
        "owner": "string",
        "surface_kind": "string",
        "source_sha256": "string; must match task.source_sha256",
        "runtime": "string",
        "status": "classified | not_classified | error",
        "durable_rules": [
            {
                "text": "durable project rule text",
                "topic": "canonical topic stem candidate",
                "scope": "file-scoped | topic-based | on-request | root-only | discard",
                "glob": "file glob for file-scoped rules, otherwise null",
                "kind": "safety | workflow | style | command | architecture | config | provider",
                "confidence": "high | medium | low",
                "sources": ["source file paths"],
                "source_quote": "short quote or close paraphrase from source",
            }
        ],
        "discarded": [{"text": "discarded text", "reason": "why discarded", "source_quote": "evidence"}],
        "conflicts": ["meaningful unresolved conflicts"],
        "notes": ["classifier notes"],
    }


def classifier_instructions() -> list[str]:
    return [
        "Extract only durable project rules and facts from the source content.",
        "Discard provider boilerplate, source-of-truth redirects, duplicate pointers, and generic AI advice.",
        "Preserve concrete commands, paths, ports, approvals, safety restrictions, scopes, and provider gotchas.",
        "Prefer specific scopes over vague broad rules; do not weaken safety constraints.",
        "Return JSON only, matching output_contract exactly.",
        "Do not write files or propose generated provider views.",
    ]


def read_source_content(record: InventoryRecord) -> str:
    path = REPO_ROOT / record.path
    if not path.exists():
        raise ValueError(f"legacy source file is missing: {record.path}")
    text = read_text_for_markers(path)
    if len(text) > MAX_CLASSIFIER_SOURCE_CHARS:
        return text[:MAX_CLASSIFIER_SOURCE_CHARS] + "\n\n[TRUNCATED: source exceeded classifier character limit]\n"
    return text


def build_classification_task(record: InventoryRecord) -> ClassificationTask:
    return ClassificationTask(
        source_path=record.path,
        surface_id=record.surface_id,
        surface_display=record.surface_display,
        owner=record.owner,
        surface_kind=record.surface_kind,
        source_sha256=record.sha256,
        parser_hint=record.parser_hint,
        content=read_source_content(record),
        instructions=classifier_instructions(),
        output_contract=classification_output_contract(),
    )


def mock_classify(record: InventoryRecord) -> ClassificationResult:
    notes = [
        "Mock runtime only validates the classification output contract.",
        "No durable rules were extracted; use a real classifier runtime for migration.",
    ]
    return ClassificationResult(
        source_path=record.path,
        surface_id=record.surface_id,
        owner=record.owner,
        surface_kind=record.surface_kind,
        source_sha256=record.sha256,
        runtime="mock",
        status="not_classified",
        durable_rules=[],
        discarded=[],
        conflicts=[],
        notes=notes,
    )


def require_string(raw: dict[str, object], field_name: str, *, allow_empty: bool = False) -> str:
    value = raw.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"classifier result field {field_name!r} must be a string")
    if not allow_empty and not value.strip():
        raise ValueError(f"classifier result field {field_name!r} cannot be empty")
    return value


def require_enum(raw: dict[str, object], field_name: str, allowed: set[str]) -> str:
    value = require_string(raw, field_name).strip()
    if value not in allowed:
        options = ", ".join(sorted(allowed))
        raise ValueError(f"classifier result field {field_name!r} must be one of: {options}")
    return value


def list_of_strings(value: object, field_name: str, *, allow_empty_items: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"classifier result field {field_name!r} must be a list of strings")
    if not allow_empty_items and any(not item.strip() for item in value):
        raise ValueError(f"classifier result field {field_name!r} cannot contain empty strings")
    return value


def parse_extracted_rule(raw: object, task: ClassificationTask) -> ExtractedRule:
    if not isinstance(raw, dict):
        raise ValueError("durable_rules entries must be objects")
    glob = raw.get("glob")
    if glob is not None:
        if not isinstance(glob, str):
            raise ValueError("durable rule field 'glob' must be string or null")
        if not glob.strip():
            raise ValueError("durable rule field 'glob' cannot be empty when present")
    scope = require_enum(raw, "scope", ALLOWED_SCOPES)
    if scope == "file-scoped" and glob is None:
        raise ValueError("file-scoped durable rules require glob")
    if scope != "file-scoped" and glob is not None:
        raise ValueError("only file-scoped durable rules may include glob")
    sources = list_of_strings(raw.get("sources"), "durable_rules[].sources")
    if sources != [task.source_path]:
        raise ValueError("durable rule sources must match the current task source_path")
    return ExtractedRule(
        text=require_string(raw, "text"),
        topic=require_string(raw, "topic"),
        scope=scope,
        glob=glob,
        kind=require_enum(raw, "kind", ALLOWED_KINDS),
        confidence=require_enum(raw, "confidence", ALLOWED_CONFIDENCE),
        sources=sources,
        source_quote=require_string(raw, "source_quote"),
    )


def parse_discarded_rule(raw: object) -> DiscardedRule:
    if not isinstance(raw, dict):
        raise ValueError("discarded entries must be objects")
    return DiscardedRule(
        text=require_string(raw, "text"),
        reason=require_string(raw, "reason"),
        source_quote=require_string(raw, "source_quote"),
    )


def parse_classification_result(raw: object, task: ClassificationTask, runtime: str) -> ClassificationResult:
    if not isinstance(raw, dict):
        raise ValueError("classifier output must be a JSON object")
    if raw.get("source_path") != task.source_path:
        raise ValueError("classifier output source_path does not match task")
    if raw.get("surface_id") != task.surface_id:
        raise ValueError("classifier output surface_id does not match task")
    if raw.get("source_sha256") != task.source_sha256:
        raise ValueError("classifier output source_sha256 does not match task")

    durable_raw = raw.get("durable_rules", [])
    discarded_raw = raw.get("discarded", [])
    if not isinstance(durable_raw, list):
        raise ValueError("classifier result field 'durable_rules' must be a list")
    if not isinstance(discarded_raw, list):
        raise ValueError("classifier result field 'discarded' must be a list")

    status = require_enum(raw, "status", ALLOWED_STATUSES)
    if status != "classified" and durable_raw:
        raise ValueError("only status='classified' may return durable_rules")

    result_runtime = raw.get("runtime")
    if not isinstance(result_runtime, str) or not result_runtime.strip():
        result_runtime = runtime

    return ClassificationResult(
        source_path=task.source_path,
        surface_id=task.surface_id,
        owner=require_string(raw, "owner"),
        surface_kind=require_string(raw, "surface_kind"),
        source_sha256=task.source_sha256,
        runtime=result_runtime,
        status=status,
        durable_rules=[parse_extracted_rule(item, task) for item in durable_raw],
        discarded=[parse_discarded_rule(item) for item in discarded_raw],
        conflicts=list_of_strings(raw.get("conflicts", []), "conflicts"),
        notes=list_of_strings(raw.get("notes", []), "notes"),
    )


def command_classify(task: ClassificationTask, command: str, timeout: int) -> ClassificationResult:
    argv = shlex.split(command)
    if not argv:
        raise ValueError("--classifier-command cannot be empty")
    try:
        completed = subprocess.run(
            argv,
            input=json.dumps(asdict(task), indent=2, sort_keys=True),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"classifier command timed out for {task.source_path}") from exc
    except OSError as exc:
        raise ValueError(f"classifier command failed to start: {exc}") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        detail = f": {stderr}" if stderr else ""
        raise ValueError(f"classifier command failed for {task.source_path} with exit {completed.returncode}{detail}")
    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"classifier command returned invalid JSON for {task.source_path}: {exc}") from exc
    return parse_classification_result(raw, task, "command")


def classify_record(
    record: InventoryRecord,
    task: ClassificationTask,
    runtime: str,
    classifier_command: str | None,
    timeout: int,
) -> ClassificationResult:
    if runtime == "mock":
        return mock_classify(record)
    if runtime == "command":
        if not classifier_command:
            raise ValueError("--runtime command requires --classifier-command")
        return command_classify(task, classifier_command, timeout)
    raise ValueError("unsupported classifier runtime {!r}; available runtimes: mock, command".format(runtime))


def classify_run(run_id: str, runtime: str, classifier_command: str | None, timeout: int):
    if timeout <= 0:
        raise ValueError("--classifier-timeout must be greater than zero")

    run_dir, records = load_inventory(run_id)
    classify_dir = run_dir / "classifications" / "by-file"
    task_dir = run_dir / "classifications" / "tasks"
    classify_dir.mkdir(parents=True, exist_ok=True)
    task_dir.mkdir(parents=True, exist_ok=True)

    results: list[ClassificationResult] = []
    for record in records:
        if record.role != "legacy_input" or not record.can_scan_legacy:
            continue
        task = build_classification_task(record)
        task_output = task_dir / f"{safe_artifact_name(record.path)}.task.json"
        write_json(task_output, asdict(task))
        result = classify_record(record, task, runtime, classifier_command, timeout)
        results.append(result)
        output = classify_dir / f"{safe_artifact_name(record.path)}.json"
        write_json(output, asdict(result))

    index = {
        "run_id": run_id,
        "runtime": runtime,
        "classified_count": len(results),
        "classified_sources": [result.source_path for result in results],
        "created_at": utc_now(),
    }
    write_json(run_dir / "classifications" / "classification-index.json", index)
    update_manifest(
        run_dir,
        status="classified",
        classification_runtime=runtime,
        classified_count=len(results),
        classified_at=utc_now(),
    )
    return run_dir
