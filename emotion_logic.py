import cv2
import numpy as np
from fer import FER
from PIL import Image

def analyze_crowd_mood(image):
    """
    Analyzes the emotions of faces detected in the image to determine the overall crowd mood.
    
    Args:
        image: PIL Image or numpy array
        
    Returns:
        mood_stats: Dictionary with emotion percentages
        dominant_mood: The most prevalent emotion
    """
    # Convert PIL Image to OpenCV format if necessary
    if isinstance(image, Image.Image):
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    else:
        img = image.copy()

    # Initialize FER detector
    detector = FER(mtcnn=False) # mtcnn=True is more accurate but slower
    
    # Detect emotions
    results = detector.detect_emotions(img)
    
    if not results:
        return {'No Faces Detected': 100}, "Unknown"

    emotion_totals = {
        'angry': 0,
        'disgust': 0,
        'fear': 0,
        'happy': 0,
        'sad': 0,
        'surprise': 0,
        'neutral': 0
    }
    
    for face in results:
        emotions = face['emotions']
        # Find the max emotion for this face
        top_emotion = max(emotions, key=emotions.get)
        emotion_totals[top_emotion] += 1
        
    total_faces = len(results)
    mood_stats = {k: (v / total_faces) * 100 for k, v in emotion_totals.items()}
    dominant_mood = max(emotion_totals, key=emotion_totals.get)
    
    return mood_stats, dominant_mood
