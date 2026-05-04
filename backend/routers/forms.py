from __future__ import annotations

import textwrap

import fitz
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response

from models.FormModel import AdmissionFormCreate, AdmissionFormUpdate, FormField, FormSubmissionRequest
from services.auth_service import get_current_user, is_student_user
from services.document_service import normalize_doc_type
from services.form_service import (
    create_form,
    delete_form,
    get_form,
    get_student_form_response,
    get_public_form,
    list_public_forms,
    list_form_responses,
    list_forms,
    submit_form_response,
    update_form,
)
from routers.engines import queue_engine_run

router = APIRouter()


def _ensure_admin(current_user: dict):
    if (current_user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can manage forms")


def _filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value).strip("_") or "download"


def _make_application_pdf(response: dict) -> bytes:
    form = response.get("form") or {}
    response_data = response.get("response_data") or {}
    title = form.get("title") or "Admission Application"
    doc = fitz.open()
    page_width, page_height = 595, 842
    margin = 32
    y = 34
    line = (0.88, 0.9, 0.94)
    muted = (0.39, 0.43, 0.5)
    dark = (0.06, 0.09, 0.16)
    field_bg = (0.97, 0.98, 0.99)

    def new_page():
        page_obj = doc.new_page(width=page_width, height=page_height)
        page_obj.draw_rect(
            fitz.Rect(0, 0, page_width, page_height),
            color=(1, 1, 1),
            fill=(1, 1, 1),
        )
        return page_obj

    page = new_page()

    def ensure_space(required: float):
        nonlocal page, y
        if y + required <= page_height - margin:
            return
        page = new_page()
        y = margin

    def text_lines(value: object, chars: int = 38, max_lines: int = 4) -> list[str]:
        value_text = str(value if value not in (None, "") else "-")
        lines: list[str] = []
        for paragraph in value_text.splitlines() or ["-"]:
            lines.extend(textwrap.wrap(paragraph, width=chars) or [""])
        if len(lines) > max_lines:
            return lines[: max_lines - 1] + [f"{lines[max_lines - 1][: max(0, chars - 3)]}..."]
        return lines

    def draw_header():
        nonlocal y
        page.insert_text((margin, y), title, fontsize=19, fontname="helv", color=dark)
        y += 24
        meta = [
            f"Status: {response.get('status') or 'submitted'}",
            f"Student ID: {response.get('student_id') or '-'}",
            f"Reference: {response.get('application_reference') or '-'}",
        ]
        page.insert_text((margin, y), "   |   ".join(meta), fontsize=8.5, fontname="helv", color=muted)
        y += 22

    def draw_field(x: float, top: float, width: float, label: str, value: object) -> float:
        lines = text_lines(value)
        height = max(42, 29 + len(lines) * 11)
        rect = fitz.Rect(x, top, x + width, top + height)
        page.draw_rect(rect, color=field_bg, fill=field_bg)
        page.insert_text((x + 8, top + 16), str(label or "Field").upper()[:46], fontsize=7.8, fontname="helv", color=muted)
        text_y = top + 32
        for line_text in lines:
            page.insert_text((x + 8, text_y), line_text, fontsize=10.5, fontname="helv", color=dark)
            text_y += 11
        return height

    def draw_section(section_name: str, fields: list[dict]):
        nonlocal y
        visible_fields = [field for field in fields if field.get("field_type") != "file"]
        if not visible_fields:
            return
        column_gap = 14
        section_padding = 14
        column_width = (page_width - (margin * 2) - (section_padding * 2) - column_gap) / 2
        prepared = []
        for field in sorted(visible_fields, key=lambda item: int(item.get("sort_order") or 0)):
            value = response_data.get(field.get("field_key"), "")
            lines = text_lines(value)
            prepared.append((field, max(42, 29 + len(lines) * 11)))
        rows = [prepared[index : index + 2] for index in range(0, len(prepared), 2)]
        row_heights = [max(item[1] for item in row) for row in rows]
        section_height = 51 + sum(row_heights) + max(0, len(row_heights) - 1) * 12 + section_padding
        ensure_space(section_height + 14)
        section_top = y
        section_rect = fitz.Rect(margin, section_top, page_width - margin, section_top + section_height)
        page.draw_rect(section_rect, color=line, width=0.8)
        page.insert_text((margin + section_padding, section_top + 26), section_name, fontsize=15, fontname="helv", color=dark)
        row_y = section_top + 49
        for row, row_height in zip(rows, row_heights):
            for col, (field, _) in enumerate(row):
                x = margin + section_padding + col * (column_width + column_gap)
                draw_field(x, row_y, column_width, field.get("label") or field.get("field_key") or "Field", response_data.get(field.get("field_key"), ""))
            row_y += row_height + 12
        y = section_top + section_height + 16

    draw_header()

    fields_by_section: dict[str, list[dict]] = {}
    for field in form.get("fields", []):
        fields_by_section.setdefault(field.get("section") or "General", []).append(field)

    if not fields_by_section:
        draw_section(
            "Application Details",
            [
                {"field_key": key, "label": key.replace("_", " ").title(), "sort_order": index}
                for index, key in enumerate(sorted(response_data))
                if key != "_custom"
            ],
        )
    else:
        for section, fields in fields_by_section.items():
            draw_section(section, fields)

    payload = doc.tobytes(deflate=True)
    doc.close()
    return payload


def _doc_bytes_to_pdf(payload: bytes, mime_type: str | None, object_key: str | None) -> bytes | None:
    if not payload:
        return None
    lower_key = (object_key or "").lower()
    media = (mime_type or "").lower()
    try:
        if media == "application/pdf" or lower_key.endswith(".pdf") or payload.startswith(b"%PDF-"):
            source = fitz.open(stream=payload, filetype="pdf")
            out = fitz.open()
            out.insert_pdf(source)
            result = out.tobytes(deflate=True)
            source.close()
            out.close()
            return result

        image_type = "png"
        if media == "image/jpeg" or lower_key.endswith((".jpg", ".jpeg")) or payload[:3] == b"\xff\xd8\xff":
            image_type = "jpeg"
        elif media == "image/png" or lower_key.endswith(".png"):
            image_type = "png"
        image_doc = fitz.open(stream=payload, filetype=image_type)
        pdf_bytes = image_doc.convert_to_pdf()
        image_doc.close()
        return pdf_bytes
    except Exception:
        return None


def _merged_documents_pdf(response: dict, request: Request, include_application: bool = True) -> bytes:
    merged = fitz.open()
    if include_application:
        app_doc = fitz.open(stream=_make_application_pdf(response), filetype="pdf")
        merged.insert_pdf(app_doc)
        app_doc.close()

    providers = getattr(request.app.state, "storage_providers", {})
    active_provider_name = getattr(request.app.state.storage, "name", "")
    providers.setdefault(active_provider_name, request.app.state.storage)

    for document in response.get("documents") or []:
        provider = providers.get(document.get("provider"))
        if not provider:
            continue
        payload = provider.get_bytes(document.get("object_key") or "")
        pdf_payload = _doc_bytes_to_pdf(payload or b"", document.get("mime_type"), document.get("object_key"))
        if not pdf_payload:
            continue
        doc = fitz.open(stream=pdf_payload, filetype="pdf")
        merged.insert_pdf(doc)
        doc.close()

    if len(merged) == 0:
        raise HTTPException(status_code=404, detail="No downloadable documents found")
    result = merged.tobytes(deflate=True)
    merged.close()
    return result


def _download_response(payload: bytes, filename: str, media_type: str = "application/pdf") -> Response:
    return Response(
        content=payload,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{_filename(filename)}"'},
    )


@router.get("/forms")
async def get_forms(current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    return {"forms": list_forms()}


@router.post("/forms")
async def create_admission_form(payload: AdmissionFormCreate, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    return {"form": create_form(payload, current_user.get("username") or "")}


@router.get("/forms/{form_id}")
async def get_admission_form(form_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    form = get_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return {"form": form}


@router.put("/forms/{form_id}")
async def update_admission_form(form_id: str, payload: AdmissionFormUpdate, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    return {"form": update_form(form_id, payload)}


@router.put("/forms/{form_id}/fields")
async def update_admission_form_fields(form_id: str, fields: list[FormField], current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    return {"form": update_form(form_id, AdmissionFormUpdate(fields=fields))}


@router.delete("/forms/{form_id}")
async def delete_admission_form(form_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    delete_form(form_id)
    return {"message": "Form deleted"}


@router.post("/forms/{form_id}/publish")
async def publish_admission_form(form_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    return {"form": update_form(form_id, AdmissionFormUpdate(status="published"))}


@router.post("/forms/{form_id}/unpublish")
async def unpublish_admission_form(form_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    return {"form": update_form(form_id, AdmissionFormUpdate(status="draft"))}


@router.get("/forms/{form_id}/responses")
async def get_form_responses(form_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_admin(current_user)
    return {"responses": list_form_responses(form_id)}


@router.get("/forms/{form_id}/responses/me")
async def get_my_form_response(form_id: str, current_user: dict = Depends(get_current_user)):
    if not is_student_user(current_user):
        raise HTTPException(status_code=403, detail="Only student users can view their submitted form")
    response = get_student_form_response(form_id, current_user)
    if not response:
        raise HTTPException(status_code=404, detail="Submitted form not found")
    return {"response": response}


@router.get("/forms/{form_id}/responses/me/application.pdf")
async def download_my_application_pdf(form_id: str, current_user: dict = Depends(get_current_user)):
    if not is_student_user(current_user):
        raise HTTPException(status_code=403, detail="Only student users can download their submitted form")
    response = get_student_form_response(form_id, current_user, include_private_document_fields=True)
    if not response:
        raise HTTPException(status_code=404, detail="Submitted form not found")
    filename = f"{response.get('student_id') or 'student'}_{response.get('form', {}).get('slug') or 'application'}.pdf"
    return _download_response(_make_application_pdf(response), filename)


@router.get("/forms/{form_id}/responses/me/documents.pdf")
async def download_my_documents_pdf(
    form_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if not is_student_user(current_user):
        raise HTTPException(status_code=403, detail="Only student users can download their documents")
    response = get_student_form_response(form_id, current_user, include_private_document_fields=True)
    if not response:
        raise HTTPException(status_code=404, detail="Submitted form not found")
    filename = f"{response.get('student_id') or 'student'}_{response.get('form', {}).get('slug') or 'documents'}_documents.pdf"
    return _download_response(_merged_documents_pdf(response, request, include_application=False), filename)


@router.get("/forms/{form_id}/responses/me/documents/{doc_type}/download")
async def download_my_document(
    form_id: str,
    doc_type: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if not is_student_user(current_user):
        raise HTTPException(status_code=403, detail="Only student users can download their documents")
    response = get_student_form_response(form_id, current_user, include_private_document_fields=True)
    if not response:
        raise HTTPException(status_code=404, detail="Submitted form not found")
    normalized_doc_type = normalize_doc_type(doc_type)
    document = next((doc for doc in response.get("documents") or [] if doc.get("doc_type") == normalized_doc_type), None)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    providers = getattr(request.app.state, "storage_providers", {})
    active_provider_name = getattr(request.app.state.storage, "name", "")
    providers.setdefault(active_provider_name, request.app.state.storage)
    provider = providers.get(document.get("provider"))
    if not provider:
        raise HTTPException(status_code=500, detail=f"Storage provider not configured: {document.get('provider')}")
    payload = provider.get_bytes(document.get("object_key") or "")
    if not payload:
        raise HTTPException(status_code=404, detail="Document file not found")
    suffix = "pdf" if (document.get("mime_type") == "application/pdf") else "jpg"
    if document.get("mime_type") == "image/png":
        suffix = "png"
    filename = f"{response.get('student_id') or 'student'}_{normalized_doc_type}.{suffix}"
    return _download_response(payload, filename, document.get("mime_type") or "application/octet-stream")


@router.get("/public/forms/{slug}")
async def get_published_form(slug: str):
    return {"form": get_public_form(slug)}


@router.get("/public/forms")
async def get_published_forms():
    return {"forms": list_public_forms()}


@router.post("/forms/{form_id}/responses")
async def submit_admission_form_response(
    form_id: str,
    payload: FormSubmissionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    if not is_student_user(current_user):
        raise HTTPException(status_code=403, detail="Only student users can submit admission forms")
    result = submit_form_response(form_id, payload.response_data, current_user)
    queue_engine_run(background_tasks, result["student_id"], request, current_user, [])
    return result
