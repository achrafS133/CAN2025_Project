import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
from sms_alerts import send_threat_alert

# Load the YOLOv8 model (Nano version for speed)
model = YOLO('yolov8n.pt')

def detect_threats(image):
    """
    Detects people and potential threats (knives, scissors, bottles) in an image.
    
    Args:
        image: PIL Image or numpy array
        
    Returns:
        processed_img: Image with bounding boxes
        stats: Dictionary containing detection statistics
    """
    # Convert PIL Image to OpenCV format if necessary
    if isinstance(image, Image.Image):
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    else:
        img = image.copy()

    # Define classes of interest
    PERSON_CLASS = 0
    THREAT_CLASSES = [39, 43, 76]  # 39: bottle, 43: knife, 76: scissors
    # Note: YOLOv8 COCO classes mapping:
    # 0: person, 39: bottle, 43: knife, 76: scissors

    results = model(img)[0]
    
    people_count = 0
    found_threats = []
    
    for box in results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        
        # Get coordinates
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        if cls == PERSON_CLASS:
            people_count += 1
            # Draw Green box for People
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"Person {conf:.2f}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        elif cls in THREAT_CLASSES:
            label = results.names[cls]
            found_threats.append(label)
            # Draw Red box for Threats
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3) # Thicker box for emphasis
            cv2.putText(img, f"WARNING: {label.upper()}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Send SMS Alert (Only once per session usually, but here we trigger per call)
            send_threat_alert(label)

    # Convert back to RGB for Streamlit display
    processed_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    stats = {
        'people_count': people_count,
        'threats': list(set(found_threats)),
        'crowd_warning': people_count > 50,
        'threat_detected': len(found_threats) > 0
    }
    
    return processed_img, stats
