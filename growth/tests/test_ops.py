import io
import os
import sys
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ops

class GrowthOpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=str(Path(self.tmp.name)/"db"/"crm.db")
    def tearDown(self):
        self.tmp.cleanup()
    def runcli(self,*args):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            return ops.main(["--db",self.db,*args])
    def test_crm_approval_and_suppression(self):
        self.assertEqual(self.runcli("init"),0)
        self.assertEqual(self.runcli("lead-add","--name","Test Co-op","--type","organization","--source","test","--email","hello@example.org","--consent","business-relevant"),0)
        self.assertEqual(self.runcli("draft","--lead-id","1","--subject","Pilot?","--body","Could we connect?"),0)
        self.assertEqual(self.runcli("send","--id","1","--confirm"),1) # not approved
        self.assertEqual(self.runcli("approve","--id","1"),0)
        self.assertEqual(self.runcli("approve","--id","1"),1)
        self.assertEqual(self.runcli("send","--id","1"),1) # no confirm
        self.assertEqual(self.runcli("suppress","--email","hello@example.org","--reason","opt-out"),0)
        self.assertEqual(self.runcli("send","--id","1","--confirm"),1)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT state FROM drafts").fetchone()[0],"cancelled")
            self.assertEqual(con.execute("SELECT count(*) FROM events").fetchone()[0],4)
        self.assertEqual(self.runcli("stats"),0)
    def test_unknown_lead_and_validation(self):
        self.assertEqual(self.runcli("draft","--lead-id","99","--subject","S","--body","B"),1)
        self.assertEqual(self.runcli("lead-add","--name","Test","--type","org","--source","site","--email","not-an-email","--consent","unknown"),1)
    def test_no_send_without_smtp(self):
        self.runcli("lead-add","--name","Test","--type","org","--source","site","--email","test@example.org","--consent","business-relevant")
        self.runcli("draft","--lead-id","1","--subject","Hello","--body","Test")
        self.runcli("approve","--id","1")
        clean={k:os.environ.pop(k,None) for k in ("SMTP_HOST","SMTP_PORT","SMTP_USER","SMTP_PASSWORD","SMTP_FROM","SMTP_POSTAL_ADDRESS")}
        try:
            self.assertEqual(self.runcli("send","--id","1","--confirm"),1)
        finally:
            for k,v in clean.items():
                if v is not None: os.environ[k]=v
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT state FROM drafts").fetchone()[0],"approved")

if __name__=="__main__": unittest.main()
