
## Vega

**Leg Layout**

L0---L1

   *

L3---L2

Clockwise from 0 to 3 starting with front left.

0 - Front Left

1 - Front Right

2 - Rear Right

3 - Rear Left


### YOLO

```
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "storage-driver": "overlay2",
  "data-root": "/var/lib/docker",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "no-new-privileges": true,
  "experimental": false
}
```

https://github.com/Seeed-Projects/jetson-examples/blob/main/reComputer/scripts/ultralytics-yolo/README.md
https://forums.developer.nvidia.com/t/integrating-yolov8-for-real-time-obstacle-avoidance-in-isaac-sim/308907

### Video Query

How to run it:

python3 -m nano_llm.agents.video_query --api=mlc \
    --model Efficient-Large-Model/VILA1.5-3b \
    --max-context-len 256 \
    --max-new-tokens 32 \
    --video-input csi://0 \
    --video-output webrtc://@:8554/output

### FIX FOR yolo on 36.4.4 jetpack 6

```

Hi,

jetson-examples is expected to work since r36.4.0 is compatible with r36.4.4.
Please try to modify the files below to apply the trick:

Edit /home/nvidia/.local/lib/python3.10/site-packages/reComputer/scripts/ultralytics-yolo/run.sh
@@ -4,13 +4,13 @@ CONTAINER_NAME="ultralytics-yolo"
 
 # Function to get L4T version
 get_l4t_version() {
-    local l4t_version=""
-    local release_line=$(head -n 1 /etc/nv_tegra_release)
-    if [[ $release_line =~ R([0-9]+)\ *\(release\),\ REVISION:\ ([0-9]+\.[0-9]+) ]]; then
-        local major="${BASH_REMATCH[1]}"
-        local revision="${BASH_REMATCH[2]}"
-        l4t_version="${major}.${revision}"
-    fi
+    local l4t_version="36.4.0"
+    #local release_line=$(head -n 1 /etc/nv_tegra_release)
+    #if [[ $release_line =~ R([0-9]+)\ *\(release\),\ REVISION:\ ([0-9]+\.[0-9]+) ]]; then
+    #    local major="${BASH_REMATCH[1]}"
+    #    local revision="${BASH_REMATCH[2]}"
+    #    l4t_version="${major}.${revision}"
+    #fi
     echo "$l4t_version"
 }
Edit /home/nvidia/.local/lib/python3.10/site-packages/reComputer/scripts/utils.sh
@@ -72,7 +72,7 @@ check_base_env()
 
         L4T_RELEASE=$(echo "$L4T_VERSION_STRING" | cut -f 2 -d ' ' | grep -Po '(?<=R)[^;]+')
         L4T_REVISION=$(echo "$L4T_VERSION_STRING" | cut -f 2 -d ',' | grep -Po '(?<=REVISION: )[^;]+')
-        L4T_VERSION="$L4T_RELEASE.$L4T_REVISION"
+        L4T_VERSION="36.4.0"
 
     elif [ "$ARCH" = "x86_64" ]; then
         echo "${RED}Unsupported architecture: $ARCH${RESET}"
Run with below command:
$ reComputer run ultralytics-yolo
INFO: machine[nvidia jetson agx orin developer kit] confirmed...
run example：ultralytics-yolo
----example init----
CONFIG_FILE_PATH=/home/nvidia/.local/lib/python3.10/site-packages/reComputer/scripts/ultralytics-yolo/config.yaml
yq is already installed.
jq is already installed.
jq-1.6
32.6.1 35.3.1 35.4.1 35.5.0 36.3.0 36.4.0
L4T VERSION 36.4.0 is in the allowed: OK!
nvidia-jetpack is installed: OK!
Required 16GB/1640GB disk space: OK!
Required 2GB/29GB memory space: OK!
/etc/docker/daemon.json already exists and has the correct content.
Docker is installed and the current user has permissions to use it.
----example start----
Detected L4T version: 36.4.0
Using Docker image: yaohui1998/ultralytics-jetpack61:v1.0
v1.0: Pulling from yaohui1998/ultralytics-jetpack61
...
Container ultralytics-yolo does not exist. Creating and starting...
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 ```


 ### Run CSI on vl42

 # Install
sudo apt install v4l2loopback-dkms

# Load module
sudo modprobe v4l2loopback video_nr=10 card_label="CSI"

# Check it exists
ls /dev/video10

# Stream CSI to it (keep this running)
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! \
    'video/x-raw(memory:NVMM),width=640,height=480,framerate=30/1' ! \
    nvvidconv ! 'video/x-raw,format=I420' ! \
    v4l2sink device=/dev/video10