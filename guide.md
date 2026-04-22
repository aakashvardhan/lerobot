# SO-101 Robot Arm Setup Guide

Hardware: SO-101 follower arm + SO-101 leader arm + 2x OpenCV cameras
Ports (may change on reboot — re-run `ls /dev/cu.usbmodem*` to confirm):
- Follower: `/dev/cu.usbmodem5B3E1225231`
- Leader: `/dev/cu.usbmodem5B3E1218771`

---

## 1. Find USB Ports

```bash
ls /dev/cu.usbmodem*
```

---

## 2. Scan for Motors on a Port

Useful for debugging — connect one motor at a time to identify its current ID.

```bash
uv run python - << 'EOF'
from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

bus = FeetechMotorsBus(
    port="/dev/cu.usbmodem5B3E1225231",  # change to target port
    motors={"dummy": Motor(1, "sts3215", MotorNormMode.DEGREES)},
)
bus._connect(handshake=False)
result = bus.broadcast_ping()
print(f"Found motors (id: model_number): {result}")
bus.disconnect()
EOF
```

---

## 3. Reassign a Motor ID

Use when a motor has a wrong or duplicate ID. Connect **only that one motor** to the controller board first.

Motor name → target ID mapping for SO-101:

| Motor name    | Target ID |
|---------------|-----------|
| shoulder_pan  | 1         |
| shoulder_lift | 2         |
| elbow_flex    | 3         |
| wrist_flex    | 4         |
| wrist_roll    | 5         |
| gripper       | 6         |

```bash
uv run python - << 'EOF'
from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

bus = FeetechMotorsBus(
    port="/dev/cu.usbmodem5B3E1225231",  # change to target port
    motors={
        "wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),  # change name and target ID
    }
)
bus.setup_motor("wrist_roll", initial_baudrate=1_000_000, initial_id=6)  # initial_id = current wrong ID
print("Done")
EOF
```

### Guided setup (all motors, one at a time)

Prompts you to connect each motor individually and assigns IDs automatically:

```bash
# Follower arm
lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/cu.usbmodem5B3E1225231 --robot.id=my_so_arm

# Leader arm
lerobot-setup-motors --teleop.type=so101_leader --teleop.port=/dev/cu.usbmodem5B3E1218771 --teleop.id=my_so_arm_leader
```

---

## 4. Calibrate Follower Arm

```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/cu.usbmodem5B3E1225231 --robot.id=my_so_arm
```

**Steps:**
1. Move arm to the middle of its range → press ENTER
2. Move all joints (except `wrist_roll`) through their **full range of motion**
3. Open and close the **gripper** fully
4. Press ENTER to save

Calibration saved to:
`~/.cache/huggingface/lerobot/calibration/robots/so_follower/my_so_arm.json`

---

## 5. Calibrate Leader Arm

```bash
lerobot-calibrate --teleop.type=so101_leader --teleop.port=/dev/cu.usbmodem5B3E1218771 --teleop.id=my_so_arm_leader
```

Same steps as follower. Calibration saved to:
`~/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_so_arm_leader.json`

---

## 6. Find Cameras

Scan for available camera indices:

```bash
uv run python -c "
import cv2
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Camera found at index {i}')
        cap.release()
"
```

Capture a snapshot from each to identify which is which:

```bash
uv run python -c "
import cv2
for i in [0, 1]:
    cap = cv2.VideoCapture(i)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f'camera_{i}.jpg', frame)
        print(f'Saved camera_{i}.jpg')
    cap.release()
" && open camera_0.jpg camera_1.jpg
```

---

## 7. Teleoperate

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/cu.usbmodem5B3E1225231 \
  --robot.id=my_so_arm \
  --robot.cameras.wrist_camera.type=opencv \
  --robot.cameras.wrist_camera.index_or_path=0 \
  --robot.cameras.wrist_camera.width=640 \
  --robot.cameras.wrist_camera.height=480 \
  --robot.cameras.wrist_camera.fps=30 \
  --robot.cameras.top_camera.type=opencv \
  --robot.cameras.top_camera.index_or_path=1 \
  --robot.cameras.top_camera.width=640 \
  --robot.cameras.top_camera.height=480 \
  --robot.cameras.top_camera.fps=30 \
  --teleop.type=so101_leader \
  --teleop.port=/dev/cu.usbmodem5B3E1218771 \
  --teleop.id=my_so_arm_leader
```

---

## 8. Record a Dataset

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/cu.usbmodem5B3E1225231 \
  --robot.id=my_so_arm \
  --robot.cameras.wrist_camera.type=opencv \
  --robot.cameras.wrist_camera.index_or_path=0 \
  --robot.cameras.wrist_camera.width=640 \
  --robot.cameras.wrist_camera.height=480 \
  --robot.cameras.wrist_camera.fps=30 \
  --robot.cameras.top_camera.type=opencv \
  --robot.cameras.top_camera.index_or_path=1 \
  --robot.cameras.top_camera.width=640 \
  --robot.cameras.top_camera.height=480 \
  --robot.cameras.top_camera.fps=30 \
  --teleop.type=so101_leader \
  --teleop.port=/dev/cu.usbmodem5B3E1218771 \
  --teleop.id=my_so_arm_leader \
  --repo-id=<your_hf_username>/<dataset_name>
```
