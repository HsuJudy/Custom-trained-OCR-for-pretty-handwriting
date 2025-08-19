#!/usr/bin/env python3
"""
Database service layer for the Enhanced Journaling Engine.
Handles all database operations using Prisma ORM.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

# Prisma client will be generated
try:
    from prisma import Prisma
    from prisma.models import User, Project, Image, Label, JournalEntry, ColorSticker
except ImportError:
    print("⚠️  Prisma not installed. Run: pip install prisma")
    Prisma = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for managing journal entries, labels, and color stickers."""
    
    def __init__(self):
        self.db = Prisma() if Prisma else None
        if self.db:
            self.db.connect()
    
    def __del__(self):
        if self.db:
            self.db.disconnect()
    
    # User Management
    async def create_user(self, email: str, name: str = None) -> Optional[User]:
        """Create a new user."""
        if not self.db:
            return None
        
        try:
            user = await self.db.user.create({
                'email': email,
                'name': name
            })
            logger.info(f"Created user: {email}")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def get_user(self, email: str) -> Optional[User]:
        """Get user by email."""
        if not self.db:
            return None
        
        try:
            user = await self.db.user.find_unique(where={'email': email})
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    # Project Management
    async def create_project(self, user_id: str, name: str, description: str = None) -> Optional[Project]:
        """Create a new project."""
        if not self.db:
            return None
        
        try:
            project = await self.db.project.create({
                'name': name,
                'description': description,
                'userId': user_id
            })
            logger.info(f"Created project: {name}")
            return project
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None
    
    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user."""
        if not self.db:
            return []
        
        try:
            projects = await self.db.project.find_many(
                where={'userId': user_id},
                include={'images': True, 'entries': True}
            )
            return projects
        except Exception as e:
            logger.error(f"Error getting user projects: {e}")
            return []
    
    # Image Management
    async def create_image(self, project_id: str, filename: str, original_name: str, 
                          file_size: int, mime_type: str, width: int = None, 
                          height: int = None) -> Optional[Image]:
        """Create a new image record."""
        if not self.db:
            return None
        
        try:
            image = await self.db.image.create({
                'filename': filename,
                'originalName': original_name,
                'fileSize': file_size,
                'mimeType': mime_type,
                'width': width,
                'height': height,
                'projectId': project_id
            })
            logger.info(f"Created image: {filename}")
            return image
        except Exception as e:
            logger.error(f"Error creating image: {e}")
            return None
    
    async def update_image_status(self, image_id: str, status: str) -> bool:
        """Update image processing status."""
        if not self.db:
            return False
        
        try:
            await self.db.image.update(
                where={'id': image_id},
                data={'status': status}
            )
            logger.info(f"Updated image {image_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating image status: {e}")
            return False
    
    # Label Management
    async def create_label(self, image_id: str, user_id: str, text: str, 
                          x: float, y: float, width: float, height: float,
                          confidence: float = None) -> Optional[Label]:
        """Create a new label."""
        if not self.db:
            return None
        
        try:
            label = await self.db.label.create({
                'text': text,
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'confidence': confidence,
                'imageId': image_id,
                'userId': user_id
            })
            logger.info(f"Created label: {text}")
            return label
        except Exception as e:
            logger.error(f"Error creating label: {e}")
            return None
    
    async def get_image_labels(self, image_id: str) -> List[Label]:
        """Get all labels for an image."""
        if not self.db:
            return []
        
        try:
            labels = await self.db.label.find_many(
                where={'imageId': image_id},
                include={'user': True}
            )
            return labels
        except Exception as e:
            logger.error(f"Error getting image labels: {e}")
            return []
    
    # Journal Entry Management
    async def create_journal_entry(self, image_id: str, project_id: str, entry_id: str,
                                  text_content: str, date: datetime = None,
                                  page_number: int = None, confidence: float = None,
                                  color_code: str = None, enhanced_text: str = None,
                                  sentiment: float = None, themes: List[str] = None,
                                  characters: List[str] = None, locations: List[str] = None,
                                  narrative_threads: List[str] = None) -> Optional[JournalEntry]:
        """Create a new journal entry."""
        if not self.db:
            return None
        
        try:
            entry = await self.db.journalentry.create({
                'entryId': entry_id,
                'textContent': text_content,
                'date': date,
                'pageNumber': page_number,
                'confidence': confidence,
                'colorCode': color_code,
                'enhancedText': enhanced_text,
                'sentiment': sentiment,
                'themes': themes or [],
                'characters': characters or [],
                'locations': locations or [],
                'narrativeThreads': narrative_threads or [],
                'imageId': image_id,
                'projectId': project_id
            })
            logger.info(f"Created journal entry: {entry_id}")
            return entry
        except Exception as e:
            logger.error(f"Error creating journal entry: {e}")
            return None
    
    async def get_project_entries(self, project_id: str) -> List[JournalEntry]:
        """Get all journal entries for a project."""
        if not self.db:
            return []
        
        try:
            entries = await self.db.journalentry.find_many(
                where={'projectId': project_id},
                include={'image': True},
                order=[{'date': 'asc'}]
            )
            return entries
        except Exception as e:
            logger.error(f"Error getting project entries: {e}")
            return []
    
    async def update_journal_entry(self, entry_id: str, **kwargs) -> bool:
        """Update a journal entry."""
        if not self.db:
            return False
        
        try:
            await self.db.journalentry.update(
                where={'entryId': entry_id},
                data=kwargs
            )
            logger.info(f"Updated journal entry: {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating journal entry: {e}")
            return False
    
    # Color Sticker Management
    async def create_color_sticker(self, image_id: str, color: str, color_hex: str,
                                  x: float, y: float, width: float, height: float,
                                  confidence: float) -> Optional[ColorSticker]:
        """Create a new color sticker record."""
        if not self.db:
            return None
        
        try:
            sticker = await self.db.colorsticker.create({
                'color': color,
                'colorHex': color_hex,
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'confidence': confidence,
                'imageId': image_id
            })
            logger.info(f"Created color sticker: {color}")
            return sticker
        except Exception as e:
            logger.error(f"Error creating color sticker: {e}")
            return None
    
    async def get_image_color_stickers(self, image_id: str) -> List[ColorSticker]:
        """Get all color stickers for an image."""
        if not self.db:
            return []
        
        try:
            stickers = await self.db.colorsticker.find_many(
                where={'imageId': image_id}
            )
            return stickers
        except Exception as e:
            logger.error(f"Error getting image color stickers: {e}")
            return []
    
    # Analytics and Reporting
    async def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get analytics for a project."""
        if not self.db:
            return {}
        
        try:
            # Get project data
            project = await self.db.project.find_unique(
                where={'id': project_id},
                include={
                    'images': {
                        'include': {
                            'labels': True,
                            'entries': True,
                            'colorStickers': True
                        }
                    }
                }
            )
            
            if not project:
                return {}
            
            # Calculate analytics
            total_images = len(project.images)
            total_labels = sum(len(img.labels) for img in project.images)
            total_entries = len(project.entries)
            total_stickers = sum(len(img.colorStickers) for img in project.images)
            
            # Get unique themes and colors
            all_themes = []
            all_colors = []
            
            for entry in project.entries:
                all_themes.extend(entry.themes)
                if entry.colorCode:
                    all_colors.append(entry.colorCode)
            
            unique_themes = list(set(all_themes))
            unique_colors = list(set(all_colors))
            
            return {
                'project_id': project_id,
                'project_name': project.name,
                'total_images': total_images,
                'total_labels': total_labels,
                'total_entries': total_entries,
                'total_stickers': total_stickers,
                'unique_themes': unique_themes,
                'unique_colors': unique_colors,
                'theme_count': len(unique_themes),
                'color_count': len(unique_colors),
                'created_at': project.createdAt.isoformat(),
                'updated_at': project.updatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting project analytics: {e}")
            return {}
    
    # Data Export
    async def export_project_data(self, project_id: str) -> Dict[str, Any]:
        """Export all project data for OCR training."""
        if not self.db:
            return {}
        
        try:
            project = await self.db.project.find_unique(
                where={'id': project_id},
                include={
                    'images': {
                        'include': {
                            'labels': True,
                            'entries': True,
                            'colorStickers': True
                        }
                    }
                }
            )
            
            if not project:
                return {}
            
            # Structure data for export
            export_data = {
                'project_info': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'created_at': project.createdAt.isoformat()
                },
                'images': [],
                'labels': [],
                'entries': [],
                'color_stickers': []
            }
            
            for image in project.images:
                # Image data
                export_data['images'].append({
                    'id': image.id,
                    'filename': image.filename,
                    'original_name': image.originalName,
                    'width': image.width,
                    'height': image.height,
                    'status': image.status.value
                })
                
                # Labels for this image
                for label in image.labels:
                    export_data['labels'].append({
                        'id': label.id,
                        'text': label.text,
                        'x': label.x,
                        'y': label.y,
                        'width': label.width,
                        'height': label.height,
                        'confidence': label.confidence,
                        'image_id': image.id
                    })
                
                # Journal entries for this image
                for entry in image.entries:
                    export_data['entries'].append({
                        'id': entry.id,
                        'entry_id': entry.entryId,
                        'text_content': entry.textContent,
                        'enhanced_text': entry.enhancedText,
                        'date': entry.date.isoformat() if entry.date else None,
                        'color_code': entry.colorCode,
                        'themes': entry.themes,
                        'characters': entry.characters,
                        'locations': entry.locations,
                        'sentiment': entry.sentiment,
                        'image_id': image.id
                    })
                
                # Color stickers for this image
                for sticker in image.colorStickers:
                    export_data['color_stickers'].append({
                        'id': sticker.id,
                        'color': sticker.color,
                        'color_hex': sticker.colorHex,
                        'x': sticker.x,
                        'y': sticker.y,
                        'width': sticker.width,
                        'height': sticker.height,
                        'confidence': sticker.confidence,
                        'image_id': image.id
                    })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting project data: {e}")
            return {}


# Singleton instance
db_service = DatabaseService()
