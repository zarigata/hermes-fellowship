#!/usr/bin/env python3
"""Offline, single-message-at-a-time SchoolBox CRM and approval queue. Python stdlib only."""
import argparse
import datetime as dt
import os
from pathlib import Path
import sqlite3
import ssl
import smtplib
import sys
from email.message import EmailMessage

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
 source TEXT NOT NULL, email TEXT, consent TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'research', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS drafts(
 id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL REFERENCES leads(id),
 subject TEXT NOT NULL, body TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL,
 approved_at TEXT, sent_at TEXT);
CREATE TABLE IF NOT EXISTS suppression(
 email TEXT PRIMARY KEY, reason TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, object_id INTEGER,
 detail TEXT NOT NULL, at TEXT NOT NULL);
"""

def connect(db):
    path = Path(db).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() and path.is_symlink():
        raise ValueError("Database may not be a symbolic link")
    if path.exists():
        os.chmod(path, 0o600)
    con = sqlite3.connect(str(path), timeout=10)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    os.chmod(path, 0o600)
    return con

def log(con, kind, obj, detail):
    con.execute("INSERT INTO events(kind,object_id,detail,at) VALUES (?,?,?,?)",
                (kind, obj, detail, now()))

def execute(args, con):
    cmd = args.command
    if cmd == "init":
        print("Database ready (private files only).")
    elif cmd == "lead-add":
        if args.email and ("\n" in args.email or "\r" in args.email or "@" not in args.email):
            raise ValueError("Invalid email")
        with con:
            c = con.execute("INSERT INTO leads(name,type,source,email,consent,created_at) VALUES (?,?,?,?,?,?)",
              (args.name,args.type,args.source,args.email.lower() if args.email else None,args.consent,now()))
            log(con,"lead_added",c.lastrowid,"new lead; no contact sent")
        print(f"Lead #{c.lastrowid} saved.")
    elif cmd == "leads":
        for x in con.execute("SELECT id,name,type,source,email,status FROM leads ORDER BY id"):
            print("\t".join(str(v or "") for v in x))
    elif cmd == "draft":
        lead = con.execute("SELECT email FROM leads WHERE id=?", (args.lead_id,)).fetchone()
        if not lead: raise ValueError("Unknown lead id")
        if not lead[0]: raise ValueError("Lead has no contact email")
        with con:
            c=con.execute("INSERT INTO drafts(lead_id,subject,body,created_at) VALUES (?,?,?,?)",
              (args.lead_id,args.subject,args.body,now()))
            log(con,"draft_created",c.lastrowid,"new unapproved draft")
        print(f"Draft #{c.lastrowid} pending human approval.")
    elif cmd == "queue":
        for x in con.execute("SELECT d.id,l.name,l.email,d.subject,d.state FROM drafts d JOIN leads l ON l.id=d.lead_id ORDER BY d.id"):
            print("\t".join(str(v) for v in x))
    elif cmd == "show":
        r=con.execute("SELECT d.id,l.name,l.email,d.subject,d.body,d.state FROM drafts d JOIN leads l ON d.lead_id=l.id WHERE d.id=?", (args.id,)).fetchone()
        if not r: raise ValueError("Unknown draft")
        print("Draft #%s\nLead: %s\nTo: %s\nSubject: %s\nBody:\n%s\nState: %s" % r)
    elif cmd == "approve":
        r=con.execute("SELECT state FROM drafts WHERE id=?", (args.id,)).fetchone()
        if not r or r[0] != "draft": raise ValueError("Only unapproved drafts can be approved")
        with con:
            con.execute("UPDATE drafts SET state='approved',approved_at=? WHERE id=?", (now(),args.id))
            log(con,"approved",args.id,"reviewed by CLI operator")
        print(f"Draft #{args.id} approved. Not sent.")
    elif cmd == "suppress":
        e=args.email.strip().lower()
        if "@" not in e: raise ValueError("Invalid email")
        with con:
            con.execute("INSERT INTO suppression(email,reason,created_at) VALUES(?,?,?) ON CONFLICT(email) DO UPDATE SET reason=excluded.reason",
                        (e,args.reason,now()))
            con.execute("UPDATE drafts SET state='cancelled' WHERE state IN ('draft','approved') AND lead_id IN (SELECT id FROM leads WHERE email=?)",(e,))
            log(con,"suppressed",None,e)
        print("Suppressed; queued drafts cancelled.")
    elif cmd == "send":
        if not args.confirm: raise ValueError("Send requires --confirm and prior approval")
        r=con.execute("""SELECT d.state,l.email,d.subject,d.body,l.consent
          FROM drafts d JOIN leads l ON d.lead_id=l.id WHERE d.id=?""",(args.id,)).fetchone()
        if not r or r[0]!="approved": raise ValueError("Draft must be approved and not already sent")
        _,to,subject,body,consent=r
        if not to or con.execute("SELECT 1 FROM suppression WHERE email=?",(to,)).fetchone():
            raise ValueError("No eligible recipient")
        if consent.strip().lower() in ("", "unknown", "none", "no", "opted-out"):
            raise ValueError("Consent/contact basis must be recorded and reviewed")
        needed=["SMTP_HOST","SMTP_PORT","SMTP_USER","SMTP_PASSWORD","SMTP_FROM","SMTP_POSTAL_ADDRESS"]
        missing=[k for k in needed if not os.getenv(k)]
        if missing: raise ValueError("Missing SMTP config: "+", ".join(missing))
        if any(c in subject for c in "\r\n"): raise ValueError("Invalid subject")
        m=EmailMessage()
        m["From"]=os.environ["SMTP_FROM"]
        m["To"]=to
        m["Subject"]=subject
        m.set_content(body.rstrip()+"\n\n"+os.environ["SMTP_POSTAL_ADDRESS"]+"\nTo opt out, reply STOP.\n")
        port=int(os.environ["SMTP_PORT"])
        if port != 465: raise ValueError("Starter supports TLS-on-connect port 465 only")
        # Mark attempted before network call: a timeout is ambiguous; NEVER auto-retry.
        with con:
            con.execute("UPDATE drafts SET state='send_attempted' WHERE id=? AND state='approved'",(args.id,))
            log(con,"send_attempted",args.id,"SMTP request initiated; uncertain failures need manual reconciliation")
        with smtplib.SMTP_SSL(os.environ["SMTP_HOST"],port,context=ssl.create_default_context(),timeout=20) as smtp:
            smtp.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
            smtp.send_message(m)
        with con:
            con.execute("UPDATE drafts SET state='sent',sent_at=? WHERE id=?",(now(),args.id))
            log(con,"sent",args.id,"SMTP server accepted message")
        print("SMTP accepted one email; delivery not guaranteed.")
    elif cmd == "stats":
        for table in ("leads","drafts","suppression"):
            print(f"{table}: {con.execute('SELECT count(*) FROM '+table).fetchone()[0]}")
        for status,count in con.execute("SELECT state,count(*) FROM drafts GROUP BY state ORDER BY state"):
            print(f"  {status}: {count}")
    else:
        raise ValueError("Unrecognized command")

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="./private/growth.db")
    sub=p.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    la=sub.add_parser("lead-add")
    for flag in ("name","type","source","consent"):
        la.add_argument("--"+flag,required=True)
    la.add_argument("--email")
    sub.add_parser("leads")
    dr=sub.add_parser("draft"); dr.add_argument("--lead-id",type=int,required=True)
    dr.add_argument("--subject",required=True); dr.add_argument("--body",required=True)
    sub.add_parser("queue")
    for cmd in ("show","approve"):
        sub.add_parser(cmd).add_argument("--id",required=True,type=int)
    sp=sub.add_parser("suppress");sp.add_argument("--email",required=True);sp.add_argument("--reason",default="opt-out")
    se=sub.add_parser("send");se.add_argument("--id",required=True,type=int);se.add_argument("--confirm",action="store_true")
    sub.add_parser("stats")
    args=p.parse_args(argv)
    try:
        with connect(args.db) as con: execute(args,con)
    except (ValueError,sqlite3.Error,OSError,smtplib.SMTPException) as exc:
        print("ERROR: "+str(exc),file=sys.stderr);return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
