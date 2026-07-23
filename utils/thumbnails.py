from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import io
import logging

logger = logging.getLogger(__name__)


class ThumbnailsMixin:
    """
    A mixin class that provides thumbnail generation and management functionality for Django models.
    
    This mixin enables automatic creation, regeneration, and cleanup of thumbnails for both PDF and 
    image file attachments. Thumbnails are generated at a standard size of 400x300px and are stored 
    as JPEG files for optimal web performance.
    
    Features:
    - Automatic thumbnail generation for PDF and image formats
    - Support for local filesystem and cloud storage (S3, etc.)
    - Smart caching to avoid regenerating existing thumbnails
    - Placeholder generation for unsupported file types
    - Comprehensive error handling and logging
    - Orphaned thumbnail cleanup
    - Batch thumbnail management
    
    Usage:
    1. Inherit from ThumbnailsMixin in your Django model
    2. Implement _get_mapping_field_names() to define file-to-thumbnail field mappings
    3. Call create_thumbnails() to generate thumbnails for file attachments
    
    Example:
        class Document(models.Model, ThumbnailsMixin):
            file = models.FileField(upload_to='documents/')
            thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
            
            def _get_mapping_field_names(self):
                return {
                    'file': 'thumbnail',
                }
    
    Supported File Types:
    - PDF: Generates thumbnail from first page
    - JPEG, PNG, GIF, BMP, TIFF, WebP: Direct image thumbnail generation
    - Other formats: Generates placeholder thumbnail
    
    Thumbnail Specifications:
    - Size: 400px × 300px (landscape)
    - Format: JPEG
    - Quality: 85
    - Background: White (for content with aspect ratio mismatch)
    
    Attributes:
        None (uses model fields defined by child class)
    
    Methods:
        - create_thumbnails(force=False): Generate thumbnails for all mapped files
        - delete_all_thumbnails(): Remove all thumbnails and clear thumbnail fields
        - regenerate_thumbnails(): Regenerate all thumbnails (delete old, create new)
        - cleanup_orphaned_thumbnails(): Remove thumbnails without source files
        - get_thumbnail_info(): Get detailed info about current thumbnails
        - _delete_old_thumbnail(thumbnail_field): Delete a single old thumbnail
        - _create_single_thumbnail(file_obj): Create thumbnail for one file
        - _create_pdf_thumbnail(pdf_content): Generate thumbnail from PDF content
        - _create_image_thumbnail(image_content): Generate thumbnail from image content
        - _resize_to_thumbnail(image): Resize image to thumbnail dimensions with aspect ratio preservation
        - _create_placeholder_thumbnail(): Generate placeholder for unsupported files
        - _is_image_file(file_content): Detect if content is a valid image file
    """
    
    def _get_mapping_field_names(self):
        return {}

    def create_thumbnails(self, force=False):
        """
        Create thumbnails for all attachment files
        Supports PDF and image formats
        Thumbnail size: 400px x 300px (landscape)
        """
        # Refresh instance from database to ensure latest data
        # Important for background tasks that might receive stale instance
        if self.pk:
            self.refresh_from_db()
            logger.info(f"Refreshed instance from database: {self.__class__.__name__} {self.pk}")
        
        # Mapping file field to thumbnail field
        file_mappings = self._get_mapping_field_names()
        if not file_mappings:
            logger.warning("No file to thumbnail mappings defined.")
            return None
        
        thumb_fields = []
        for file_field, thumb_field in file_mappings.items():
            file_obj = getattr(self, file_field)
            thumb_fields.append(thumb_field)
            
            if file_obj and file_obj.name:
                try:
                    # Check if thumbnail already exists
                    existing_thumb = getattr(self, thumb_field)
                    
                    # If force=True or no thumbnail exists, create a new one
                    should_create = force or not (existing_thumb and existing_thumb.name)
                    
                    if not should_create:
                        # Skip if thumbnail already exists and force is not set
                        continue
                    
                    # Delete old thumbnail if exists
                    if existing_thumb and existing_thumb.name:
                        self._delete_old_thumbnail(existing_thumb)
                        logger.info(f"Deleted old thumbnail: {existing_thumb.name}")
                    
                    # Generate new thumbnail
                    thumbnail = self._create_single_thumbnail(file_obj)
                    
                    if thumbnail:
                        # Generate thumbnail filename
                        base_name = os.path.splitext(os.path.basename(file_obj.name))[0]
                        thumb_name = f"{base_name}_thumb.jpg"
                        
                        # Save thumbnail
                        setattr(self, thumb_field, ContentFile(thumbnail, name=thumb_name))
                        logger.info(f"Thumbnail created for {file_field}: {thumb_name}")
                    
                except Exception as e:
                    logger.error(f"Error creating thumbnail for {file_field}: {str(e)}")
                    continue
        
        # Save model with new thumbnails
        if thumb_fields:
            self.save(update_fields=thumb_fields)

    def _delete_old_thumbnail(self, thumbnail_field):
        """
        delete old thumbnail file from storage
        """
        try:
            if thumbnail_field and thumbnail_field.name:
                # Check if file exists in storage before deleting
                if default_storage.exists(thumbnail_field.name):
                    # Delete the file from storage
                    default_storage.delete(thumbnail_field.name)
                    logger.info(f"Successfully deleted old thumbnail file: {thumbnail_field.name}")
                else:
                    logger.warning(f"Thumbnail file not found in storage: {thumbnail_field.name}")
                
        except Exception as e:
            logger.error(f"Error deleting old thumbnail: {str(e)}")

    def delete_all_thumbnails(self):
        """
        Delete all thumbnails and clear thumbnail fields
        """
        file_mappings = self._get_mapping_field_names()
        if not file_mappings:
            return
        
        deleted_count = 0
        for file_field, thumb_field in file_mappings.items():
            try:
                existing_thumb = getattr(self, thumb_field)
                if existing_thumb and existing_thumb.name:
                    self._delete_old_thumbnail(existing_thumb)
                    # Clear field
                    setattr(self, thumb_field, None)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting thumbnail for {thumb_field}: {str(e)}")
        
        if deleted_count > 0:
            # Update cleared fields
            thumb_fields = [thumb_field for file_field, thumb_field in file_mappings.items()]
            self.save(update_fields=thumb_fields)
            logger.info(f"Deleted {deleted_count} thumbnails for {self.__class__.__name__} {self.pk}")

    def regenerate_thumbnails(self):
        """
        Regenerate all thumbnails (delete old + create new)
        """
        logger.info(f"Regenerating thumbnails for {self.__class__.__name__} {self.pk}")
        self.create_thumbnails(force=True)

    def cleanup_orphaned_thumbnails(self):
        """
        Cleanup thumbnails without source files
        """
        file_mappings = self._get_mapping_field_names()
        if not file_mappings:
            return
        
        cleaned_count = 0
        for file_field, thumb_field in file_mappings.items():
            try:
                file_obj = getattr(self, file_field)
                existing_thumb = getattr(self, thumb_field)
                
                # If thumbnail exists but source file is missing, delete thumbnail
                if existing_thumb and existing_thumb.name and (not file_obj or not file_obj.name):
                    self._delete_old_thumbnail(existing_thumb)
                    setattr(self, thumb_field, None)
                    cleaned_count += 1
                    logger.info(f"Cleaned orphaned thumbnail for {thumb_field}")
                    
            except Exception as e:
                logger.error(f"Error cleaning orphaned thumbnail for {thumb_field}: {str(e)}")
        
        if cleaned_count > 0:
            thumb_fields = [thumb_field for file_field, thumb_field in file_mappings.items()]
            self.save(update_fields=thumb_fields)
            logger.info(f"Cleaned {cleaned_count} orphaned thumbnails")

    def get_thumbnail_info(self):
        """
        Get information about existing thumbnails
        """
        file_mappings = self._get_mapping_field_names()
        if not file_mappings:
            return {}
        
        info = {}
        for file_field, thumb_field in file_mappings.items():
            file_obj = getattr(self, file_field)
            thumb_obj = getattr(self, thumb_field)
            
            info[file_field] = {
                'has_source_file': bool(file_obj and file_obj.name),
                'source_file_name': file_obj.name if file_obj else None,
                'has_thumbnail': bool(thumb_obj and thumb_obj.name),
                'thumbnail_name': thumb_obj.name if thumb_obj else None,
                'thumbnail_exists_in_storage': (
                    default_storage.exists(thumb_obj.name) 
                    if thumb_obj and thumb_obj.name 
                    else False
                ),
                'needs_regeneration': (
                    bool(file_obj and file_obj.name) and 
                    not bool(thumb_obj and thumb_obj.name)
                )
            }
        
        return info

    def _create_single_thumbnail(self, file_obj):
        """
        Create thumbnail for a single file (PDF or image)
        """
        try:
            # Check if file exists
            if not file_obj or not file_obj.name:
                logger.warning("File object is empty or has no name")
                return self._create_placeholder_thumbnail()
            
            # Method 1: Try reading directly from the filesystem (for local storage)
            try:
                # Use file.path if available (local filesystem)
                if hasattr(file_obj, 'path') and file_obj.path:
                    file_path = file_obj.path
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        logger.info(f"Read file from path: {file_path}")
                    else:
                        logger.error(f"File not found at path: {file_path}")
                        return self._create_placeholder_thumbnail()
                else:
                    raise AttributeError("file.path not available")
                    
            except (AttributeError, ValueError, OSError) as e:
                # Method 2: Fallback to storage backend (for S3, etc.)
                logger.info(f"Fallback to storage backend for: {file_obj.name}")

                # Check if file exists in storage
                if not default_storage.exists(file_obj.name):
                    logger.error(f"File not found in storage: {file_obj.name}")
                    return self._create_placeholder_thumbnail()

                # Open file using storage backend
                with default_storage.open(file_obj.name, 'rb') as f:
                    file_content = f.read()
            
            # Determine file type and create thumbnail
            if file_content.startswith(b'%PDF'):
                # File PDF
                return self._create_pdf_thumbnail(file_content)
            elif self._is_image_file(file_content):
                # File Image
                return self._create_image_thumbnail(file_content)
            else:
                # Unrecognized file, create placeholder
                return self._create_placeholder_thumbnail()
                
        except Exception as e:
            logger.error(f"Error in _create_single_thumbnail: {str(e)}")
            return self._create_placeholder_thumbnail()

    def _create_pdf_thumbnail(self, pdf_content):
        """
        Create thumbnail from PDF (first page)
        """
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            
            if pdf_document.page_count > 0:
                # Get the first page
                first_page = pdf_document[0]
                
                # Convert to image with high DPI for better quality
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = first_page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("ppm")
                image = Image.open(io.BytesIO(img_data))
                
                # Resize to thumbnail size
                thumbnail = self._resize_to_thumbnail(image)
                
                # Convert to bytes
                output = io.BytesIO()
                thumbnail.save(output, format='JPEG', quality=85, optimize=True)
                
                pdf_document.close()
                return output.getvalue()
            
            pdf_document.close()
            return self._create_placeholder_thumbnail()
            
        except Exception as e:
            logger.error(f"Error creating PDF thumbnail: {str(e)}")
            return self._create_placeholder_thumbnail()

    def _create_image_thumbnail(self, image_content):
        """
        Create thumbnail from image file
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if needed (for CMYK, RGBA, etc.)
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Resize to thumbnail size
            thumbnail = self._resize_to_thumbnail(image)
            
            # Convert to bytes
            output = io.BytesIO()
            thumbnail.save(output, format='JPEG', quality=85, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating image thumbnail: {str(e)}")
            return self._create_placeholder_thumbnail()

    def _resize_to_thumbnail(self, image):
        """
        Resize image to thumbnail size 400x300px while maintaining aspect ratio
        """
        target_width = 400
        target_height = 300
        
        # Calculate aspect ratio
        original_width, original_height = image.size
        original_ratio = original_width / original_height
        target_ratio = target_width / target_height
        
        if original_ratio > target_ratio:
            # Image is wider, fit based on width
            new_width = target_width
            new_height = int(target_width / original_ratio)
        else:
            # Image is taller, fit based on height
            new_height = target_height
            new_width = int(target_height * original_ratio)
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create canvas with target size (400x300)
        canvas = Image.new('RGB', (target_width, target_height), color='white')
        
        # Calculate position to center image
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2

        # Paste resized image onto canvas
        canvas.paste(resized_image, (x_offset, y_offset))
        
        return canvas

    def _create_placeholder_thumbnail(self):
        """
        Create placeholder thumbnail for files that cannot be processed
        """
        try:
            # Create placeholder image with size 400x300
            image = Image.new('RGB', (400, 300), color='#f0f0f0')
            draw = ImageDraw.Draw(image)  # Create drawing context
            
            # Add placeholder text
            try:
                # Try using default font
                font = ImageFont.load_default()
            except:
                font = None
            
            # Draw simple document icon - adjusted for 400x300
            # Border
            draw.rectangle([75, 60, 325, 240], outline='#cccccc', width=2)
            
            # Document header
            draw.rectangle([75, 60, 325, 90], fill='#cccccc')
            
            # Lines to simulate text
            for i in range(5):
                y = 110 + (i * 15)
                draw.rectangle([95, y, 305, y+8], fill='#eeeeee')
            
            # Text
            text = "Document\nThumbnail"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (400 - text_width) // 2
            y = 200
            
            draw.text((x, y), text, fill='#666666', font=font, align='center')
            
            # Convert to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating placeholder: {str(e)}")
            # Return minimal 400x300 white image if error
            img = Image.new('RGB', (400, 300), 'white')
            output = io.BytesIO()
            img.save(output, format='JPEG')
            return output.getvalue()

    def _is_image_file(self, file_content):
        """
        Check if the file is an image based on magic number
        """
        # Magic numbers for common image formats
        image_signatures = [
            b'\xFF\xD8\xFF',  # JPEG
            b'\x89PNG\r\n\x1A\n',  # PNG
            b'GIF87a',  # GIF87a
            b'GIF89a',  # GIF89a
            b'BM',  # BMP
            b'II*\x00',  # TIFF (little endian)
            b'MM\x00*',  # TIFF (big endian)
            b'RIFF',  # WebP (will be followed by WEBP)
        ]
        
        for signature in image_signatures:
            if file_content.startswith(signature):
                return True
        
        # Special check for WebP
        if file_content.startswith(b'RIFF') and b'WEBP' in file_content[:12]:
            return True
        
        return False