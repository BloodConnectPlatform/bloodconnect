from typing import List, Optional
from pydantic import BaseModel, Field


class LegalSection(BaseModel):
    title: str = Field(..., description="Heading of the section")
    content: str = Field(..., description="Descriptive text for the section")
    points: Optional[List[str]] = Field(None, description="Detailed bullet points if applicable")


class LegalDocumentResponse(BaseModel):
    title: str = Field(..., description="Document title")
    last_updated: str = Field(..., description="Effective date / last update date")
    platform_name: str = Field("BloodConnect", description="Name of the platform")
    summary: str = Field(..., description="Brief executive summary of the document")
    sections: List[LegalSection] = Field(..., description="List of legal sections")
