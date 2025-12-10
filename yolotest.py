import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)  # or "/dev/video0"

print(f"Opened: {cap.isOpened()}")

if cap.isOpened():
    ret, frame = cap.read()
    print(f"Got frame: {ret}, shape: {frame.shape if ret else 'N/A'}")

cap.release()