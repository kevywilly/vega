from ultralytics import YOLO
from jetson_utils import videoSource, videoOutput, cudaFromNumpy, cudaToNumpy
import atexit
import asyncio
from settings import settings
import os

#settings.update({'weights_dir': '/data/models/yolo'})
model = YOLO("/data/models/yolo/yolo11s.pt")

INPUT_WIDTH = 1280
INPUT_HEIGHT = 720
INPUT_FRAMEWEIGHT = 60
video_output_width = 960
video_output_height = 540

#model = YOLO("yolo11s.pt")

class YoloAgent:
    def __init__(
        self,
        video_input="csi://0",
        video_output="webrtc://@:8554/output",
        video_output_width=640,
        video_output_height=360,
        video_input_width=640,
        video_input_height=360,
        video_input_framerate=60,
        **kwargs,
    ):
        # Input from CSI camera
        self.video_source = videoSource(
            video_input,
            options={
                'width': video_input_width,
                'height': video_input_height,
                'framerate': video_input_framerate,
                'flipMethod': None
            },
        )

        # Output via WebRTC
        self.output = videoOutput(
            video_output,
            options={'codec': 'h264', 'width': video_output_width, 'height': video_output_height}
        )

        self.running = False
        atexit.register(self.cleanup)

    def work(self):
        img = self.video_source.Capture()
        if img is None:
            return
        
        # Convert to numpy for YOLO
        frame = cudaToNumpy(img)
        
        # Run YOLO
        results = model(frame, imgsz=640, verbose=False)
        
        # Draw boxes
        annotated = results[0].plot()
        
        # Convert back to CUDA and output
        cuda_img = cudaFromNumpy(annotated)
        self.output.Render(cuda_img)

    
    def run(self):
        self.running = True
        while self.running:
            # Capture frame
            self.work()

            if not self.video_source.IsStreaming() or not self.output.IsStreaming():
                break

            
    async def run_async(self):
        self.run
        while self.running:
            # Capture frame
            self.work()

            if not self.video_source.IsStreaming() or not self.output.IsStreaming():
                break

            await asyncio.sleep(0)  # Yield control to the event loop
    
    def stop(self):
        self.running = False

    def cleanup(self):
        self.running = False
        try:
            if self.output:
                self.output.Close()
        except:  # noqa: E722
            pass
        