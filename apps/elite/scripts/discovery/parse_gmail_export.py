#!/usr/bin/env python3
"""
Parse Gmail Export - Sovereign Sanctuary Elite

Parse Google Takeout Gmail export (MBOX format) and index for legal search.

Usage:
    1. Export Gmail via Google Takeout (https://takeout.google.com)
    2. Select "Mail" and choose MBOX format
    3. Download and extract the archive
    4. Run: python parse_gmail_export.py <path_to_mbox_file>

Version: 1.0.0
Author: Manus AI for Architect
"""

import mailbox
import json
import re
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Legal search keywords
LEGAL_KEYWORDS = [
    "contract", "agreement", "nda", "confidential", "legal", "claim",
    "invoice", "payment", "evidence", "proof", "witness", "court",
    "solicitor", "lawyer", "attorney", "dispute", "settlement",
    "sovereign", "sanctuary", "fortress", "trading", "investment",
    "property", "tenerife", "vera de erques", "urbanismo",
]


def sha256_string(data: str) -> str:
    """Calculate SHA-256 hash of a string"""
    return hashlib.sha256(data.encode("utf-8", errors="ignore")).hexdigest()


def extract_email_metadata(message) -> Optional[Dict[str, Any]]:
    """Extract metadata from an email message"""
    try:
        # Get basic headers
        subject = message.get("Subject", "(No Subject)")
        from_addr = message.get("From", "")
        to_addr = message.get("To", "")
        date_str = message.get("Date", "")
        message_id = message.get("Message-ID", "")
        
        # Parse date
        try:
            date_obj = parsedate_to_datetime(date_str)
            date_iso = date_obj.isoformat()
        except Exception:
            date_iso = date_str
        
        # Get body preview
        body_preview = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_preview = payload.decode("utf-8", errors="ignore")[:500]
                        break
        else:
            payload = message.get_payload(decode=True)
            if payload:
                body_preview = payload.decode("utf-8", errors="ignore")[:500]
        
        # Check for legal relevance
        full_text = f"{subject} {from_addr} {to_addr} {body_preview}".lower()
        legal_matches = [kw for kw in LEGAL_KEYWORDS if kw in full_text]
        
        # Get attachments
        attachments = []
        if message.is_multipart():
            for part in message.walk():
                filename = part.get_filename()
                if filename:
                    attachments.append(filename)
        
        return {
            "message_id": message_id,
            "subject": subject,
            "from": from_addr,
            "to": to_addr,
            "date": date_iso,
            "body_preview": body_preview[:200] + "..." if len(body_preview) > 200 else body_preview,
            "attachments": attachments,
            "legal_keywords": legal_matches,
            "legal_priority": 1 if legal_matches else 5,
            "hash": sha256_string(f"{message_id}{subject}{date_str}"),
        }
    except Exception as e:
        return None


def parse_mbox(mbox_path: str) -> Dict[str, Any]:
    """Parse MBOX file and build index"""
    print(f"Parsing: {mbox_path}")
    
    mbox = mailbox.mbox(mbox_path)
    
    index = {
        "metadata": {
            "source": mbox_path,
            "parsed_at": datetime.utcnow().isoformat() + "Z",
            "total_messages": 0,
            "legal_relevant": 0,
        },
        "messages": [],
        "by_sender": defaultdict(list),
        "by_keyword": defaultdict(list),
        "legal_priority_1": [],
    }
    
    for i, message in enumerate(mbox):
        if i % 100 == 0:
            print(f"  Processing message {i}...")
        
        metadata = extract_email_metadata(message)
        if metadata:
            index["messages"].append(metadata)
            index["metadata"]["total_messages"] += 1
            
            # Index by sender
            sender = metadata["from"]
            index["by_sender"][sender].append(i)
            
            # Index by legal keyword
            for kw in metadata["legal_keywords"]:
                index["by_keyword"][kw].append(i)
            
            # Track legal priority 1
            if metadata["legal_priority"] == 1:
                index["legal_priority_1"].append(i)
                index["metadata"]["legal_relevant"] += 1
    
    # Convert defaultdicts
    index["by_sender"] = dict(index["by_sender"])
    index["by_keyword"] = dict(index["by_keyword"])
    
    return index


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_gmail_export.py <path_to_mbox_file>")
        print("\nTo get MBOX file:")
        print("  1. Go to https://takeout.google.com")
        print("  2. Deselect all, then select 'Mail'")
        print("  3. Click 'All Mail data included' → Select labels or 'All Mail'")
        print("  4. Choose MBOX format")
        print("  5. Create export and download")
        print("  6. Extract the .zip and find the .mbox file")
        return 1
    
    mbox_path = sys.argv[1]
    
    if not Path(mbox_path).exists():
        print(f"Error: File not found: {mbox_path}")
        return 1
    
    print("\n" + "=" * 60)
    print("GMAIL EXPORT PARSER - LEGAL SEARCH INDEX")
    print("=" * 60)
    
    # Parse MBOX
    index = parse_mbox(mbox_path)
    
    # Save index
    output_path = Path(mbox_path).with_suffix(".legal_index.json")
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "-" * 60)
    print("PARSING COMPLETE")
    print(f"  Total Messages: {index['metadata']['total_messages']}")
    print(f"  Legal Relevant: {index['metadata']['legal_relevant']}")
    print(f"  Unique Senders: {len(index['by_sender'])}")
    print(f"  Index saved to: {output_path}")
    
    # Show top legal keywords
    if index["by_keyword"]:
        print("\nTop Legal Keywords Found:")
        sorted_kw = sorted(index["by_keyword"].items(), key=lambda x: -len(x[1]))[:10]
        for kw, msgs in sorted_kw:
            print(f"  {kw}: {len(msgs)} messages")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
