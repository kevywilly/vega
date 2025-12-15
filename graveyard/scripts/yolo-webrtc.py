import cv2
from ultralytics import YOLO
from jetson_utils import videoSource, videoOutput, cudaFromNumpy, cudaToNumpy, cudaAllocMapped

model = YOLO("yolo11n.pt")

#model = YOLO("yolo11s.pt")

# Input from CSI camera
camera = videoSource("csi://0")

# Output via WebRTC
output = videoOutput("webrtc://@:8554/output")

while True:
    # Capture frame
    img = camera.Capture()
    if img is None:
        continue
    
    # Convert to numpy for YOLO
    frame = cudaToNumpy(img)
    
    # Run YOLO
    results = model(frame, imgsz=640, verbose=False)
    
    # Draw boxes
    annotated = results[0].plot()
    
    # Convert back to CUDA and output
    cuda_img = cudaFromNumpy(annotated)
    output.Render(cuda_img)

    if not camera.IsStreaming() or not output.IsStreaming():
        break