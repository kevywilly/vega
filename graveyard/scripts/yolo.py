import cv2
from ultralytics import YOLO

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=640,
    display_height=480,
    framerate=30,
    flip_method=0
):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, "
        f"format=NV12, framerate={framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
        f"videoconvert ! "
        f"video/x-raw, format=BGR ! appsink drop=1"
    )

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Failed to open camera!")
    exit()

print("Running... Ctrl+C to stop")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    results = model(frame, imgsz=640, verbose=False)
    
    for r in results:
        for box in r.boxes:
            # Class and confidence
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = model.names[cls]
            
            # Bounding box (pixel coordinates)
            x, y, w, h = box.xywh[0].tolist()
            
            # Normalized x position for left/right/center
            x_norm = box.xywhn[0][0].item()
            
            if x_norm < 0.33:
                position = "RIGHT"
            elif x_norm > 0.66:
                position = "LEFT"
            else:
                position = "CENTER"
            
            print(f"{name}: conf={conf:.2f} x={x:.1f} y={y:.1f} w={w:.1f} h={h:.1f} [{position}]")

cap.release()