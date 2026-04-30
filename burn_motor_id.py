"""
Reliably burn a motor ID to EEPROM on a Feetech STS3215 motor.

Connect ONLY the target motor to the controller board before running.

Usage:
    uv run python burn_motor_id.py --port /dev/cu.usbmodem5B3E1225231 --current-id 6 --target-id 5
"""

import argparse
import time

import scservo_sdk as scs

# STS3215 register addresses
ADDR_TORQUE_ENABLE = 40  # SRAM
ADDR_LOCK = 55           # SRAM — controls EEPROM write-protect
ADDR_ID = 5              # EPROM
ADDR_BAUD_RATE = 6       # EPROM

BAUDRATE = 1_000_000
PROTOCOL_END = 0  # STS uses protocol 0


def make_handlers(port, baudrate):
    ph = scs.PortHandler(port)
    pkt = scs.PacketHandler(PROTOCOL_END)
    if not ph.openPort():
        raise ConnectionError(f"Cannot open port {port}")
    ph.setBaudRate(baudrate)
    return ph, pkt


def write_byte(ph, pkt, motor_id, addr, value, label=""):
    comm, err = pkt.write1ByteTxRx(ph, motor_id, addr, value)
    if comm != scs.COMM_SUCCESS:
        raise ConnectionError(f"Write {label} failed: {pkt.getTxRxResult(comm)}")
    if err:
        print(f"  Warning writing {label}: {pkt.getRxPacketError(err)}")


def read_byte(ph, pkt, motor_id, addr, label=""):
    val, comm, err = pkt.read1ByteTxRx(ph, motor_id, addr)
    if comm != scs.COMM_SUCCESS:
        raise ConnectionError(f"Read {label} failed: {pkt.getTxRxResult(comm)}")
    return val


def burn_id(port, current_id, target_id):
    print(f"\nConnecting to {port}...")
    ph, pkt = make_handlers(port, BAUDRATE)

    # Step 1: Ping to confirm motor is present
    model, comm, err = pkt.ping(ph, current_id)
    if comm != scs.COMM_SUCCESS:
        raise RuntimeError(f"Motor {current_id} not found on bus. Is only this motor connected?")
    print(f"  Found motor at ID {current_id} (model={model})")

    # Step 2: Disable torque (required before EEPROM write)
    print(f"  Disabling torque on ID {current_id}...")
    write_byte(ph, pkt, current_id, ADDR_TORQUE_ENABLE, 0, "Torque_Enable")
    time.sleep(0.05)

    # Step 3: Unlock EEPROM (Lock=0)
    print(f"  Unlocking EEPROM (Lock=0)...")
    write_byte(ph, pkt, current_id, ADDR_LOCK, 0, "Lock")
    time.sleep(0.05)

    # Step 4: Verify Lock is 0
    lock_val = read_byte(ph, pkt, current_id, ADDR_LOCK, "Lock")
    if lock_val != 0:
        raise RuntimeError(f"EEPROM unlock failed — Lock register reads {lock_val}, expected 0")
    print(f"  EEPROM unlocked confirmed.")

    # Step 5: Write new ID to EEPROM
    print(f"  Writing ID {current_id} → {target_id}...")
    write_byte(ph, pkt, current_id, ADDR_ID, target_id, "ID")
    time.sleep(0.1)

    # Step 6: Re-lock EEPROM (Lock=1) — using new ID now
    print(f"  Re-locking EEPROM (Lock=1) on new ID {target_id}...")
    write_byte(ph, pkt, target_id, ADDR_LOCK, 1, "Lock")
    time.sleep(0.05)

    # Step 7: Read back ID to verify
    id_val = read_byte(ph, pkt, target_id, ADDR_ID, "ID")
    if id_val != target_id:
        raise RuntimeError(f"Verification failed — ID reads {id_val}, expected {target_id}")
    print(f"  ID verified: reads back as {id_val}")

    ph.closePort()
    print(f"\nSuccess! Motor ID permanently burned: {current_id} → {target_id}")
    print("Power-cycle the motor to confirm the ID persists.")


def main():
    parser = argparse.ArgumentParser(description="Burn Feetech STS3215 motor ID to EEPROM")
    parser.add_argument("--port", required=True, help="Serial port, e.g. /dev/cu.usbmodem5B3E1225231")
    parser.add_argument("--current-id", type=int, required=True, help="Current motor ID on the bus")
    parser.add_argument("--target-id", type=int, required=True, help="Target motor ID to assign")
    args = parser.parse_args()

    burn_id(args.port, args.current_id, args.target_id)


if __name__ == "__main__":
    main()
