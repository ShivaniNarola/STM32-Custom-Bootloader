import socket

SERVER_IP = "10.34.21.70"
SERVER_PORT = 5678
IMAGE_FILE = "ota_image.bin"

CHUNK_SIZE = 512

START_CMD = b"START\n"  # initial start command from client
READY_CMD = b"A"         # client signals ready for next chunk


def main():
    with open(IMAGE_FILE, "rb") as f:
        firmware = f.read()

    file_size = len(firmware)
    print(f"Firmware size: {file_size} bytes")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((SERVER_IP, SERVER_PORT))
    srv.listen(1)

    print(f"OTA Server listening on port {SERVER_PORT}...")
    conn, addr = srv.accept()
    print(f"Client connected from {addr}")

    # ---- WAIT FOR START ----
    print("Waiting for START command from client...")
    cmd = conn.recv(64)

    print("START received. Sending first chunk...")

    sent = 0
    chunk_id = 0

    # ---- SEND FIRST CHUNK IMMEDIATELY ----
    chunk = firmware[sent:sent + CHUNK_SIZE]
    conn.sendall(chunk)
    print(f"[TX] Chunk {chunk_id}, {len(chunk)} bytes")
    sent += len(chunk)
    chunk_id += 1

    # ---- SEND REMAINING CHUNKS BASED ON CLIENT READY ----
    while sent < file_size:
        try:
            ready = conn.recv(64)
        except ConnectionResetError:
            print("Client disconnected unexpectedly")
            break

        if not ready or ready.strip() != READY_CMD.strip():
            print("Client not ready or disconnected. Stopping transfer.")
            break

        # Send next chunk
        chunk = firmware[sent:sent + CHUNK_SIZE]
        conn.sendall(chunk)
        print(f"[TX] Chunk {chunk_id}, {len(chunk)} bytes")

        sent += len(chunk)
        chunk_id += 1

    print("OTA transfer finished")

    conn.close()
    srv.close()


if __name__ == "__main__":
    main()
