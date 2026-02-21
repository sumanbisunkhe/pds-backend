import face_recognition
import numpy as np
from PIL import Image
import io
import os

class FaceRecognitionService:
    @staticmethod
    def get_face_locations(image, model_default="hog"):
        """
        Intelligent face detection:
        1. Try HOG (Fast, Low RAM)
        2. If 0 faces found, try CNN on a tiny version of image (Accurate, High RAM)
        """
        # 1. Try HOG first
        face_locations = face_recognition.face_locations(image, model=model_default)
        
        if len(face_locations) == 0:
            print("HOG found nothing. Attempting CNN fallback on tiny image...")
            # We don't resize the actual image passed to encodings, 
            # but we use a tiny version to FIND the locations, then scale them back.
            # However, face_recognition.face_locations handles the model.
            # To avoid RAM explosion, we process the CNN at a lower "upsample" or on a resized frame.
            try:
                # If HOG fails, we try CNN. We use model="cnn" which is memory intensive.
                # On 1GB RAM, this WILL crash without Swap.
                face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=0, model="cnn")
            except Exception as e:
                print(f"CNN Fallback failed (likely OOM): {e}")
                return []
                
        return face_locations

    @staticmethod
    def get_face_encodings(image_bytes, num_jitters=1):
        """
        Generates face encodings using the Hybrid Detection strategy.
        """
        try:
            # Load the image
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            
            # Use Hybrid Detection to find locations first
            model_default = os.getenv("DETECTION_MODEL_DEFAULT", "hog")
            face_locations = FaceRecognitionService.get_face_locations(image, model_default=model_default)
            
            if not face_locations:
                return []

            # Generate encodings for those specific locations
            encodings = face_recognition.face_encodings(image, known_face_locations=face_locations, num_jitters=num_jitters)
            
            return encodings
        except Exception as e:
            print(f"Error generating face encodings: {e}")
            return []

    @staticmethod
    def compare_faces(known_encoding, unknown_encodings, tolerance=0.6):
        """
        Compares a known face encoding against a list of unknown encodings.
        Returns indices of matches.
        """
        matches = face_recognition.compare_faces(unknown_encodings, known_encoding, tolerance=tolerance)
        return matches

    @staticmethod
    def calculate_face_distance(known_encoding, unknown_encodings):
        """
        Calculates Euclidean distance between encodings.
        """
        return face_recognition.face_distance(unknown_encodings, known_encoding)

    @staticmethod
    def resize_image(image_bytes, max_size=(1080, 1080)):
        """
        Resizes image to speed up processing.
        """
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(max_size)
        
        # Convert to RGB if it's RGBA (transparent) to avoid JPEG save error
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        output = io.BytesIO()
        img.save(output, format="JPEG")
        return output.getvalue()
