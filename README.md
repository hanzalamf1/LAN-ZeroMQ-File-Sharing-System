# ZeroMQ-Based File Sharing System (REQ/REP)

This project is a **file sharing system** developed using the REQ/REP (Request-Reply) messaging pattern of ZeroMQ. The main goal of the system is to provide **reliable, atomic, and error-resistant** file transfer between two endpoints. The server-side is controlled by the `seed.py` script, and the client-side is managed by the `peer.py` script to activate the system.

The system detects active servers on the network, splits files into chunks for transmission, validates each chunk separately, and checks the integrity of the file after transfer.

---

## ⚙️ Technologies Used

- **ZeroMQ (REQ/REP Pattern)**: Communication between Peer and Seed is carried out using the REQ/REP pattern. This ensures that every request (file chunk) always receives a response (accept/reject).
- **Base64 + JSON Packaging**: File chunks are transmitted in JSON format and Base64 encoded.
- **Adler-32 Checksum**: An Adler-32 checksum value is attached to each file chunk for integrity verification.
- **ZIP Structural Testing**: After file transfer, the integrity of the archive is checked to ensure the structure has not been corrupted.

---

## 🔁 Feedback & Error Control

This system employs a multi-layered **feedback and error control** mechanism to minimize error probabilities during data transfer:

### • Chunk-Based Validation

Each file chunk is verified on the receiving side. A checksum value is included in every chunk, and after receiving the chunk, it is recalculated and compared. If there is any mismatch, the missing or corrupted chunk is requested again. This ensures that not only the entire file but also each **individual unit** is validated.

### • Chunk-Based Acknowledgement (ACK/NACK)

With the REQ/REP model, every file chunk sent receives an acknowledgment. The server (REP) verifies the chunk and sends either an "ACK" (accept) or "NACK" (reject) response. The client knows which chunks need to be resent based on the response. This structure ensures that:

- **Lost chunks are detected and resent.**
- **Sequential transfer is maintained.**
- **Every step of the transfer is verified.**

### • Atomic Transfer Structure

The entire file transfer is considered as a single atomic operation. The transfer is not considered complete unless all chunks are successfully received. This provides **atomicity**: either the entire file is correctly received, or nothing is received. Any inconsistency in the transfer is immediately detected and reported to the user.

---

## 📊 Data Integrity & Testing Mechanisms

The system ensures data integrity with two main verification methods:

1. **Adler-32 Checksum Verification**  
   Each file chunk is transmitted with its checksum value. The receiving side recalculates the checksum and compares it. If they match, the chunk is accepted; if not, it is resent.

2. **ZIP File Structure Validation**  
   After the entire file is transferred, the received file is zipped and the archive integrity is checked. This step serves as a second validation to ensure the transferred file is valid. If any corruption is found, the system invalidates the entire transfer.

---

## ▶️ General FTP Sequence Diagram

![control](https://github.com/user-attachments/assets/c5698ddd-9d84-4dad-a20a-2d5cc1c4cdef)

---
## 🧱 Primitive Data Types & Structure

File transfer data is packaged in JSON format using Base64 encoding. The structure of each chunk includes the following elements:

![primitive types](https://github.com/user-attachments/assets/26e5e365-d525-4ea7-96d9-bbfc25b9f752)


This structure allows each chunk to be transmitted independently and later reassembled.

---

## 🛡️ Reliability

The system is designed to guarantee **reliable file transfer** even with low bandwidth. It includes the following reliability features:

 ![reliablity](https://github.com/user-attachments/assets/d9b61ba7-e218-4383-a89a-fee81a593cea)


Thus, the system ensures that it doesn't just "send" a file, but also guarantees that the file has been received **completely and intact**.

---

## 📡 System Flow: REQ/REP Pattern

The Peer sends a request to the server (seed), which processes the request and responds accordingly. This process is repeated for every file chunk. File transfer takes place over this cycle, with verification and acknowledgment at each step.

![line disipline](https://github.com/user-attachments/assets/7c30c766-d07d-47d3-bcc1-5ad191086f58)


---

## ▶️ Error Control Diagram

![error control 2](https://github.com/user-attachments/assets/38053e30-16bd-4f83-a3a6-086071217849)


---

## ▶️ Atomicity Diagram

![atomicty](https://github.com/user-attachments/assets/eec3f72e-77fb-4c61-9a2d-ab559d934d1c)


---

## 📝 License

This project is licensed under the MIT License. It can be freely used, modified, and distributed for non-commercial purposes.
