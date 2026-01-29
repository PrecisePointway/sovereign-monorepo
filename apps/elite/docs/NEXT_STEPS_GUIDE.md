# Next Steps for Complete Coverage

**Version:** 1.0.0
**Date:** 2026-01-25
**Status:** ACTION REQUIRED

---

## 1. Overview

This guide provides detailed instructions for completing the three remaining discovery and deployment tasks:

1. **Gmail Discovery:** Exporting and indexing your Gmail data
2. **Local/NAS Discovery:** Scanning your PCs and Network Attached Storage
3. **GitHub Push:** Pushing the complete IDE handover pack to your GitHub repository

---

## 2. Gmail Discovery: Export and Index

### 2.1 Objective

To index all email communications for legal discovery readiness.

### 2.2 Procedure

#### Step 1: Export Gmail via Google Takeout

1. **Navigate to Google Takeout:**
   - Open your browser and go to [https://takeout.google.com](https://takeout.google.com)

2. **Select Data to Export:**
   - Click **"Deselect all"**
   - Scroll down to **"Mail"** and check the box
   - Click **"All Mail data included"**
   - For complete discovery, leave **"Include all messages in Mail"** selected
   - Click **"OK"**

3. **Configure Export Format:**
   - Click **"Next step"**
   - **Destination:** "Send download link via email"
   - **Frequency:** "Export once"
   - **File type & size:** ".zip" and "50 GB" (or smaller if preferred)

4. **Create and Download:**
   - Click **"Create export"**
   - Wait for the email from Google with the download link (this can take hours)
   - Download the .zip file and extract it
   - Inside the extracted folder, find the `.mbox` file (e.g., `All mail Including Spam and Trash.mbox`)

#### Step 2: Parse the MBOX File

1. **Copy the MBOX file** to the `scripts/discovery/` directory in your IDE handover pack.

2. **Run the parsing script:**
   ```bash
   cd /path/to/ide-handover-pack/scripts/discovery
   python parse_gmail_export.py "All mail Including Spam and Trash.mbox"
   ```

3. **Review the Output:**
   - A `.legal_index.json` file will be created in the same directory
   - This JSON file contains the indexed email metadata, ready for legal search

### 2.3 Key Script

- `scripts/discovery/parse_gmail_export.py`

---

## 3. Local/NAS Discovery: Scan All Machines

### 3.1 Objective

To scan all 5 PCs and your NAS for AI-related files and create a consolidated index.

### 3.2 Procedure

1. **Copy the discovery script** (`scripts/discovery/discovery_elite.ps1`) to each of your 5 PCs.

2. **Open PowerShell as Administrator** on each machine.

3. **Run the discovery script:**

   **For standard PCs:**
   ```powershell
   # Navigate to the script location
   cd C:\Path\To\Discovery\Script
   
   # Run the scan
   .\discovery_elite.ps1
   ```

   **For the PC connected to the NAS:**
   ```powershell
   .\discovery_elite.ps1 -IncludeNAS -NASPath "\\YOUR_NAS_NAME\share"
   ```

4. **Collect the Output:**
   - On each PC, a `SovereignDiscovery` folder will be created on the Desktop
   - Inside, you will find a `discovery_<hostname>_<timestamp>.json` file

5. **Consolidate the Indexes:**
   - Copy all generated `.json` files to a central location
   - These can be merged for a master view of all files across your entire infrastructure

### 3.3 Key Script

- `scripts/discovery/discovery_elite.ps1`

---

## 4. GitHub Push: Deploy to Your Repository

### 4.1 Objective

To push the complete, version-controlled IDE handover pack to your private GitHub repository.

### 4.2 Prerequisites

1. **GitHub CLI (gh):** Must be installed and authenticated (`gh auth login`)
2. **Git:** Must be installed and configured with your user details

### 4.3 Procedure

1. **Open a terminal or command prompt** in the root of the `ide-handover-pack` directory.

2. **Make the script executable (if needed):**
   ```bash
   chmod +x scripts/github_push.sh
   ```

3. **Run the push script:**

   **To create a new repository named `sovereign-sanctuary-elite`:**
   ```bash
   ./scripts/github_push.sh
   ```

   **To use a different repository name:**
   ```bash
   ./scripts/github_push.sh my-custom-repo-name
   ```

4. **Verify on GitHub:**
   - The script will output the URL to the repository
   - Navigate to the URL and confirm all files have been pushed

### 4.4 Key Script

- `scripts/github_push.sh`

---

## 5. Summary of Deliverables

| Task | Input | Script | Output |
|------|-------|--------|--------|
| Gmail Discovery | MBOX file | `parse_gmail_export.py` | `*.legal_index.json` |
| Local/NAS Discovery | Local files | `discovery_elite.ps1` | `discovery_*.json` |
| GitHub Push | IDE Pack | `github_push.sh` | GitHub Repository |

---

**Completion of these steps will provide a comprehensive, legally-discoverable archive of the entire Sovereign Sanctuary Elite ecosystem.**
