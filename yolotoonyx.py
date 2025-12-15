from ultralytics import YOLO

model = YOLO("/data/models/yolo/yolo11m.pt")
model.export(format="engine", imgsz=640)  # Creates yolo11m.engine
