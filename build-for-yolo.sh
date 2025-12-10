cd ~/jetson-containers
./run.sh --volume ~/vega:/vega $(./autotag opencv pytorch)

jetson-containers build --name=vega-yolo2 l4t-ml jetson-utils


# Install PyTorch from NVIDIA directly (not their broken index)
pip3 install --index-url https://pypi.org/simple --trusted-host pypi.org \
    https://developer.download.nvidia.com/compute/redist/jp/v60/pytorch/torch-2.3.0a0+ebedce2.nv24.05-cp310-cp310-linux_aarch64.whl

# Install ultralytics
pip3 install ultralytics --index-url https://pypi.org/simple

# Check everything works
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep -i gstreamer
python3 -c "import torch; print(torch.cuda.is_available())"

# Run your script
cd /vega
python3 yolo.py