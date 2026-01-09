import hashlib
import pymupdf
import cloudinary
import cloudinary.uploader
from groq import Groq
from config import settings
from typing import Tuple, Optional
import json
import base64
import io

# Initialize services
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

groq_client = Groq(api_key=settings.GROQ_API_KEY)

def generate_file_hash(file_content: bytes) -> str:
    """Generate SHA-256 hash of file content"""
    return hashlib.sha256(file_content + settings.SECRET_KEY.encode()).hexdigest()

def detect_file_type(file_content: bytes, filename: str) -> Tuple[str, bool]:
    """
    Detect if file is image or text-based document
    Returns: (file_type, is_processable)
    """
    # Check if it's an image first by file extension
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
    if any(filename.lower().endswith(ext) for ext in image_extensions):
        return "image", True
    
    # Try to open as PDF
    try:
        doc = pymupdf.open(stream=file_content, filetype="pdf")
        
        # Check if PDF contains images or text
        has_text = False
        has_images = False
        
        for page in doc:
            if page.get_text().strip():
                has_text = True
            if page.get_images():
                has_images = True
        
        doc.close()
        
        # If PDF has text, treat as text document
        if has_text:
            return "text", True
        # If PDF has only images, treat as image
        elif has_images:
            return "image", True
        else:
            return "text", False
            
    except:
        # Not a PDF, treat as text document
        return "text", False

def upload_to_cloudinary(file_content: bytes, filename: str, file_type: str) -> str:
    """Upload file to Cloudinary and return URL"""
    resource_type = "image" if file_type == "image" else "raw"
    
    result = cloudinary.uploader.upload(
        file_content,
        resource_type=resource_type,
        public_id=f"documents/{filename}",
        overwrite=True
    )
    
    return result["secure_url"]

def process_with_groq(file_content: bytes, file_type: str, filename: str) -> Tuple[str, str]:
    """Process file with appropriate Groq model - returns (user_response, json_data)"""
    
    if file_type == "image":
        # Use vision model for images
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # Get user-friendly response
        user_response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract invoice data in this format:\n\nITEMS:\nItem | Qty | Rate | Amount\n[item name] | [quantity] | [unit price] | [total]\n\nTOTAL: $[amount]\n\nProvide clear tabular format for all line items."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Get JSON data for backend audit
        json_response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract items and amounts from this invoice as JSON. Categorize items accurately:\n\n{\"items\": [{\"name\": \"item_name\", \"category\": \"Food/Travel/Utility/Office Supplies/Alcohol/Entertainment/Jewelry/Others\", \"amount\": 0.0}], \"total_amount\": 0.0}\n\nIMPORTANT: If you see any alcoholic beverages (wine, beer, whiskey, vodka, etc.), categorize as 'Alcohol'. If you see entertainment items (spa, massage, casino, etc.), categorize as 'Entertainment'. If you see luxury items (jewelry, designer brands, etc.), categorize as 'Jewelry'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return user_response.choices[0].message.content, json_response.choices[0].message.content
        
    else:
        # Use text model for documents
        try:
            doc = pymupdf.open(stream=file_content, filetype="pdf")
            text_content = ""
            for page in doc:
                text_content += page.get_text()
            doc.close()
        except:
            text_content = file_content.decode('utf-8', errors='ignore')
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze and summarize this document content:\n\n{text_content[:4000]}"
                }
            ],
            max_tokens=1000
        )
        
        # Get JSON data for audit
        json_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"Extract items and amounts from this document as JSON. Categorize items accurately:\n\n{{\"items\": [{{\"name\": \"item_name\", \"category\": \"Food/Travel/Utility/Office Supplies/Alcohol/Entertainment/Jewelry/Others\", \"amount\": 0.0}}], \"total_amount\": 0.0}}\n\nIMPORTANT: If you see any alcoholic beverages (wine, beer, whiskey, vodka, etc.), categorize as 'Alcohol'. If you see entertainment items (spa, massage, casino, etc.), categorize as 'Entertainment'. If you see luxury items (jewelry, designer brands, etc.), categorize as 'Jewelry'.\n\nDocument: {text_content[:2000]}"
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content, json_response.choices[0].message.content