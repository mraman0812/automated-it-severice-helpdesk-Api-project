import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.database.database import get_db
from app.models.user import User
from app.models.attachment import TicketAttachment
from app.schemas.attachment import AttachmentResponse
from app.api.deps import get_current_user
from app.services.ticket_service import TicketService
from app.services.audit_service import AuditService

router = APIRouter(tags=["Attachments"])


@router.post("/tickets/{ticket_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)

    # Read and validate file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise ValidationException(f"File size exceeds maximum {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(saved_path, "wb") as f:
        f.write(content)

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        file_name=file.filename or "unknown",
        file_path=saved_path,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.add(attachment)

    AuditService.log_action(
        db=db,
        action="ATTACHMENT_UPLOADED",
        entity_type="ticket",
        entity_id=ticket.ticket_number,
        user_id=current_user.id,
        details={"file_name": attachment.file_name, "file_size": file_size},
    )

    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/tickets/{ticket_id}/attachments", response_model=List[AttachmentResponse])
def list_attachments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)
    return db.query(TicketAttachment).filter(TicketAttachment.ticket_id == ticket.id).all()


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.query(TicketAttachment).filter(TicketAttachment.id == attachment_id).first()
    if not attachment:
        raise NotFoundException("Attachment not found", error_code="ATTACHMENT_NOT_FOUND")

    # Check permission on ticket
    TicketService.get_ticket_by_id(db=db, ticket_id=attachment.ticket_id, current_user=current_user)

    if not os.path.exists(attachment.file_path):
        raise NotFoundException("Physical file not found on server", error_code="FILE_NOT_FOUND")

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.file_name,
        media_type=attachment.file_type,
    )
