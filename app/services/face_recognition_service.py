import face_recognition
import numpy as np
from PIL import Image
import io

class FaceRecognitionService:
    @staticmethod
    def get_face_encodings(image_bytes):
        """
        Generates face encodings from image bytes.
        """
        try:
            # Load the image
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            
            # Find all face encodings in the image
            encodings = face_recognition.face_encodings(image)
            
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
        
        output = io.BytesIO()
        img.save(output, format="JPEG")
        return output.getvalue()
