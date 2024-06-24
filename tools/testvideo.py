from picamera2.outputs import FfmpegOutput
from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()
picam2.start_preview(Preview.NULL)
picam2.configure(video_config)
encoder = H264Encoder(bitrate=1000000, repeat=True, iperiod=15)
output = FfmpegOutput("-f hls -hls_time 4 -hls_list_size 5 -hls_flags delete_segments -hls_allow_cache 0 stream.m3u8")
picam2.start_recording(encoder, output)
time.sleep(9999999)