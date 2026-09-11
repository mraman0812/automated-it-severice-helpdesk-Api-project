from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
