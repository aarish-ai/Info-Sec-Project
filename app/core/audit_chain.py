import hashlib
from typing import Optional, Tuple
from app.database.db import get_db

GENESIS_HASH = "0" * 64

def compute_log_hash(
    log_id: int,
    timestamp: any,
    user_id: Optional[int],
    action: str,
    details: Optional[str],
    ip_address: Optional[str],
    prev_hash: str
) -> str:
    """
    Computes deterministic SHA-256 over canonical string concatenation
    of audit log fields.
    """
    canonical_string = (
        f"{log_id}|"
        f"{str(timestamp or '')}|"
        f"{str(user_id if user_id is not None else '')}|"
        f"{str(action or '')}|"
        f"{str(details or '')}|"
        f"{str(ip_address or '')}|"
        f"{str(prev_hash or '')}"
    )
    return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()

def append_audit_log(
    db=None,
    user_id: Optional[int] = None,
    action: str = "",
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> int:
    """
    Appends a new cryptographically hash-chained entry to the audit_log table.
    - If table is empty, prev_hash is the 64-char zero genesis block.
    - Inserts new row, reads back auto-generated log_id and timestamp,
      computes current_hash, and updates the row.
    - Commits and returns log_id.
    """
    if db is None:
        db = get_db()

    cursor = db.cursor()

    # Retrieve latest row's current_hash
    cursor.execute("SELECT current_hash FROM audit_log ORDER BY log_id DESC LIMIT 1")
    latest = cursor.fetchone()
    if latest and latest['current_hash']:
        prev_hash = latest['current_hash']
    else:
        prev_hash = GENESIS_HASH

    # Insert row with empty current_hash placeholder
    cursor.execute(
        """
        INSERT INTO audit_log (user_id, action, details, ip_address, prev_hash, current_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, action, details, ip_address, prev_hash, "")
    )
    log_id = cursor.lastrowid

    # Retrieve assigned timestamp
    cursor.execute("SELECT timestamp FROM audit_log WHERE log_id = ?", (log_id,))
    row = cursor.fetchone()
    timestamp = row['timestamp']

    # Compute hash and update
    current_hash = compute_log_hash(
        log_id=log_id,
        timestamp=timestamp,
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        prev_hash=prev_hash
    )

    cursor.execute(
        "UPDATE audit_log SET current_hash = ? WHERE log_id = ?",
        (current_hash, log_id)
    )
    db.commit()

    return log_id

def verify_audit_chain(db=None) -> Tuple[bool, int, str]:
    """
    Verifies the entire cryptographic hash chain in audit_log.
    - Reads all rows ordered by log_id ASC.
    - For row 0: verifies prev_hash == GENESIS_HASH.
    - For row i: verifies row[i].prev_hash == row[i-1].current_hash
      AND recalculates current_hash == expected_hash.
    - Returns (False, log_id, error_message) on first detected tamper.
    - Returns (True, 0, success_message) if all entries are cryptographically intact.
    """
    if db is None:
        db = get_db()

    cursor = db.cursor()
    cursor.execute(
        """
        SELECT log_id, timestamp, user_id, action, details, ip_address, prev_hash, current_hash
        FROM audit_log
        ORDER BY log_id ASC
        """
    )
    rows = cursor.fetchall()
    total_count = len(rows)

    if total_count == 0:
        return (True, 0, "All 0 audit log entries cryptographically intact")

    for i, row in enumerate(rows):
        log_id = row['log_id']

        # Genesis block check
        if i == 0:
            if row['prev_hash'] != GENESIS_HASH:
                return (
                    False,
                    log_id,
                    f"Hash chain broken at Log ID {log_id}: invalid genesis prev_hash"
                )
        else:
            prev_row = rows[i - 1]
            if row['prev_hash'] != prev_row['current_hash']:
                return (
                    False,
                    log_id,
                    f"Hash chain broken at Log ID {log_id}: prev_hash does not match previous entry"
                )

        # Recalculate hash
        expected_hash = compute_log_hash(
            log_id=row['log_id'],
            timestamp=row['timestamp'],
            user_id=row['user_id'],
            action=row['action'],
            details=row['details'],
            ip_address=row['ip_address'],
            prev_hash=row['prev_hash']
        )

        if row['current_hash'] != expected_hash:
            return (
                False,
                log_id,
                f"Hash chain broken at Log ID {log_id}: hash mismatch"
            )

    return (True, 0, f"All {total_count} audit log entries cryptographically intact")
