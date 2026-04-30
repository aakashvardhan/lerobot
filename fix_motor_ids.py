"""
Run this script when motors show up with wrong IDs after reboot.
Connect ONE motor at a time to the controller board when prompted.

Usage:
    uv run python fix_motor_ids.py
"""

from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

FOLLOWER_PORT = "/dev/cu.usbmodem5B3E1225231"
LEADER_PORT = "/dev/cu.usbmodem5B3E1218771"

FOLLOWER_MOTORS = {
    "shoulder_pan":  Motor(1, "sts3215", MotorNormMode.DEGREES),
    "shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
    "elbow_flex":    Motor(3, "sts3215", MotorNormMode.DEGREES),
    "wrist_flex":    Motor(4, "sts3215", MotorNormMode.DEGREES),
    "wrist_roll":    Motor(5, "sts3215", MotorNormMode.DEGREES),
    "gripper":       Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}

LEADER_MOTORS = {
    "shoulder_pan":  Motor(1, "sts3215", MotorNormMode.DEGREES),
    "shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
    "elbow_flex":    Motor(3, "sts3215", MotorNormMode.DEGREES),
    "wrist_flex":    Motor(4, "sts3215", MotorNormMode.DEGREES),
    "wrist_roll":    Motor(5, "sts3215", MotorNormMode.DEGREES),
    "gripper":       Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}


def scan(port, motors):
    bus = FeetechMotorsBus(port=port, motors=motors)
    bus._connect(handshake=False)
    found = bus.broadcast_ping()
    bus.disconnect()
    return found or {}


def setup_all(port, motors):
    bus = FeetechMotorsBus(port=port, motors=motors)
    for name in reversed(list(motors.keys())):
        input(f"\nConnect ONLY the '{name}' motor (target ID={motors[name].id}) and press ENTER...")
        bus.setup_motor(name)
        print(f"  '{name}' set to ID {motors[name].id}")
    print("\nAll motors set up.")


def main():
    print("=== Motor ID Fix Utility ===\n")
    print("Which arm to fix?")
    print("  1 - Follower arm")
    print("  2 - Leader arm")
    print("  3 - Scan follower (show current IDs)")
    print("  4 - Scan leader (show current IDs)")
    choice = input("\nChoice: ").strip()

    if choice == "1":
        setup_all(FOLLOWER_PORT, FOLLOWER_MOTORS)
    elif choice == "2":
        setup_all(LEADER_PORT, LEADER_MOTORS)
    elif choice == "3":
        found = scan(FOLLOWER_PORT, {"dummy": Motor(1, "sts3215", MotorNormMode.DEGREES)})
        print(f"Follower motors found: {found}")
        expected = {m.id for m in FOLLOWER_MOTORS.values()}
        missing = expected - set(found.keys())
        if missing:
            print(f"Missing IDs: {sorted(missing)}")
        else:
            print("All 6 motors present.")
    elif choice == "4":
        found = scan(LEADER_PORT, {"dummy": Motor(1, "sts3215", MotorNormMode.DEGREES)})
        print(f"Leader motors found: {found}")
        expected = {m.id for m in LEADER_MOTORS.values()}
        missing = expected - set(found.keys())
        if missing:
            print(f"Missing IDs: {sorted(missing)}")
        else:
            print("All 6 motors present.")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
