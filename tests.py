import unittest
from time import sleep
import uuid
import socket
import requests
import os

TEST_SERVER = '172.16.100.2'
TEST_ADDRESS = 'empress@empress.local'
TEST_PASSWORD = 'foo'
CA_BUNDLE = 'roles/common/files/wildcard_ca.pem'


socket.setdefaulttimeout(5)
os.environ['REQUESTS_CA_BUNDLE'] = CA_BUNDLE


class SSHTests(unittest.TestCase):
    def test_ssh_banner(self):
        """SSH is responding with its banner"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TEST_SERVER, 22))
        data = s.recv(1024)
        s.close()

        self.assertRegexpMatches(data, '^SSH-2.0-OpenSSH')


class WebTests(unittest.TestCase):
    @unittest.skip("Autoconfig isn't supported yet")
    def test_mail_autoconfig_http_and_https(self):
        """Email autoconfiguration XML file is accessible over both HTTP and HTTPS"""

        # Test getting the file over HTTP and HTTPS
        for proto in ['http', 'https']:
            r = requests.get(proto + '://autoconfig.' + TEST_SERVER + '/mail/config-v1.1.xml')

            # 200 - We should see the XML file
            self.assertEquals(r.status_code, 200)
            self.assertIn('application/xml', r.headers['Content-Type'])
            self.assertIn('clientConfig version="1.1"', r.content)


def new_message(from_email, to_email):
    """Creates an email (headers & body) with a random subject"""
    from email.mime.text import MIMEText
    msg = MIMEText('Testing')
    msg['Subject'] = uuid.uuid4().hex[:8]
    msg['From'] = from_email
    msg['To'] = to_email
    return msg.as_string(), msg['subject']


class MailTests(unittest.TestCase):
    def assertIMAPReceived(self, subject):
        """Connects with IMAP and asserts the existence of an email, then deletes it"""
        import imaplib

        sleep(1)

        # Login to IMAP
        m = imaplib.IMAP4_SSL(TEST_SERVER, 993)
        m.login(TEST_ADDRESS, TEST_PASSWORD)
        m.select()

        # Assert the message exists
        typ, data = m.search(None, '(SUBJECT \"{}\")'.format(subject))
        self.assertTrue(len(data[0].split()), 1)

        # Delete it & logout
        m.store(data[0].strip(), '+FLAGS', '\\Deleted')
        m.expunge()
        m.close()
        m.logout()

    def assertPOP3Received(self, subject):
        """Connects with POP3S and asserts the existence of an email, then deletes it"""
        import poplib

        sleep(1)

        # Login to POP3
        mail = poplib.POP3_SSL(TEST_SERVER, 995)
        mail.user(TEST_ADDRESS)
        mail.pass_(TEST_PASSWORD)

        # Assert the message exists
        num = len(mail.list()[1])
        resp, text, octets = mail.retr(num)
        self.assertTrue("Subject: " + subject in text)

        # Delete it and log out
        mail.dele(num)
        mail.quit()

    def test_imap_requires_ssl(self):
        """IMAP without SSL is NOT available"""
        import imaplib

        with self.assertRaisesRegexp(socket.timeout, 'timed out'):
            imaplib.IMAP4(TEST_SERVER, 143)

    def test_pop3_requires_ssl(self):
        """POP3 without SSL is NOT available"""
        import poplib

        with self.assertRaisesRegexp(socket.timeout, 'timed out'):
            poplib.POP3(TEST_SERVER, 110)

    def test_smtps(self):
        """Email sent from an MUA via SMTPS is delivered"""
        import smtplib
        msg, subject = new_message(TEST_ADDRESS, 'empress@empress.local')
        s = smtplib.SMTP_SSL(TEST_SERVER, 465)
        s.login(TEST_ADDRESS, TEST_PASSWORD)
        s.sendmail(TEST_ADDRESS, ['empress@empress.local'], msg)
        s.quit()
        self.assertIMAPReceived(subject)

    def test_smtps_delimiter_to(self):
        """Email sent to address with delimiter is delivered"""
        import smtplib
        msg, subject = new_message(TEST_ADDRESS, 'empress+foo@empress.local')
        s = smtplib.SMTP_SSL(TEST_SERVER, 465)
        s.login(TEST_ADDRESS, TEST_PASSWORD)
        s.sendmail(TEST_ADDRESS, ['empress+foo@empress.local'], msg)
        s.quit()
        self.assertIMAPReceived(subject)

    def test_smtps_requires_auth(self):
        """SMTPS with no authentication is rejected"""
        import smtplib
        s = smtplib.SMTP_SSL(TEST_SERVER, 465)

        with self.assertRaisesRegexp(smtplib.SMTPRecipientsRefused, 'Access denied'):
            s.sendmail(TEST_ADDRESS, ['empress@empress.local'], 'Test')

        s.quit()

    def test_smtp(self):
        """Email sent from an MTA is delivered"""
        import smtplib
        msg, subject = new_message('someone@example.com', TEST_ADDRESS)
        s = smtplib.SMTP(TEST_SERVER, 25)
        s.sendmail('someone@example.com', [TEST_ADDRESS], msg)
        s.quit()
        self.assertIMAPReceived(subject)

    def test_smtp_tls(self):
        """Email sent from an MTA via SMTP+TLS is delivered"""
        import smtplib
        msg, subject = new_message('someone@example.com', TEST_ADDRESS)
        s = smtplib.SMTP(TEST_SERVER, 25)
        s.starttls()
        s.sendmail('someone@example.com', [TEST_ADDRESS], msg)
        s.quit()
        self.assertIMAPReceived(subject)

    def test_smtps_headers(self):
        """Email sent from an MUA has DKIM and TLS headers"""
        import smtplib
        import imaplib

        # Send a message to root
        msg, subject = new_message(TEST_ADDRESS, 'empress@empress.local')
        s = smtplib.SMTP_SSL(TEST_SERVER, 465)
        s.login(TEST_ADDRESS, TEST_PASSWORD)
        s.sendmail(TEST_ADDRESS, ['empress@empress.local'], msg)
        s.quit()

        sleep(1)

        # Get the message
        m = imaplib.IMAP4_SSL(TEST_SERVER, 993)
        m.login(TEST_ADDRESS, TEST_PASSWORD)
        m.select()
        _, res = m.search(None, '(SUBJECT \"{}\")'.format(subject))
        _, data = m.fetch(res[0], '(RFC822)')

        self.assertIn(
            'DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=empress.local;',
            data[0][1]
        )

        self.assertIn(
            'DHE-RSA-AES256-GCM-SHA384 (256/256 bits)',
            data[0][1]
        )

        # Clean up
        m.store(res[0].strip(), '+FLAGS', '\\Deleted')
        m.expunge()
        m.close()
        m.logout()

    def test_smtp_headers(self):
        """Email sent from an MTA via SMTP+TLS has X-DSPAM and TLS headers"""
        import smtplib
        import imaplib

        # Send a message to root
        msg, subject = new_message('someone@example.com', TEST_ADDRESS)
        s = smtplib.SMTP(TEST_SERVER, 25)
        s.starttls()
        s.sendmail('someone@example.com', [TEST_ADDRESS], msg)
        s.quit()

        sleep(1)

        # Get the message
        m = imaplib.IMAP4_SSL(TEST_SERVER, 993)
        m.login(TEST_ADDRESS, TEST_PASSWORD)
        m.select()
        _, res = m.search(None, '(SUBJECT \"{}\")'.format(subject))
        _, data = m.fetch(res[0], '(RFC822)')

        self.assertIn(
            'X-DSPAM-Result: ',
            data[0][1]
        )

        self.assertIn(
            'ECDHE-RSA-AES256-GCM-SHA384 (256/256 bits)',
            data[0][1]
        )

        # Clean up
        m.store(res[0].strip(), '+FLAGS', '\\Deleted')
        m.expunge()
        m.close()
        m.logout()

    def test_pop3s(self):
        """Connects with POP3S and asserts the existance of an email, then deletes it"""
        import smtplib
        msg, subject = new_message(TEST_ADDRESS, 'root@empress.local')
        s = smtplib.SMTP_SSL(TEST_SERVER, 465)
        s.login(TEST_ADDRESS, TEST_PASSWORD)
        s.sendmail(TEST_ADDRESS, ['empress@empress.local'], msg)
        s.quit()
        self.assertPOP3Received(subject)
