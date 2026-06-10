from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = PROJECT_ROOT / "frontend" / "src"


def read_frontend(relative_path: str) -> str:
    path = FRONTEND_SRC / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_review_import_workspace_exists_and_uses_chinese_copy() -> None:
    page = read_frontend("app/imports/page.tsx")
    form = read_frontend("components/review-import-form.tsx")
    shell = read_frontend("components/app-shell.tsx")

    assert "评论导入" in page + form + shell
    assert "CSV" in form
    assert "JSON" in form
    assert "商品名称" in form
    assert "原始评论内容" in form
    assert "导入结果" in form
    assert "Imported" not in page + form
    assert "/imports" in shell


def test_frontend_import_client_posts_to_backend_contract() -> None:
    api = read_frontend("lib/api.ts")
    types = read_frontend("lib/types.ts")
    form = read_frontend("components/review-import-form.tsx")

    assert "importReviews" in api
    assert '"/api/imports/reviews"' in api
    assert "ReviewImportInput" in types
    assert "ReviewImportResult" in types
    assert "imported_count" in form
    assert "duplicate_count" in form
    assert "error_count" in form
    assert "review_external_ids" in form
