<!-- [![](https://travis-ci.org/taoeffect/empress.png?branch=master)](https://travis-ci.org/taoeffect/empress)
-->
Introduction
============

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/taoeffect/empress?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

**Empress is a lightweight email-focused fork of [Sovereign][sovereign]** focused on:

1. Making it __simple__ to run __your own__ secure email server.
2. Making it __simple__ to __escape__ from your existing email provider to your own server.
3. Bringing down the cost of running your own secure email server.

Some features and security fixes [may be backported to sovereign][upstream-example]. This
is not marked as a fork by GitHub because we do not intend to submit regular
pull requests upstream, or to sync all changes back from sovereign. For our
use-case, [GitHub's normal forking model doesn't work well][bad-forking].

  [sovereign]: https://github.com/al3x/sovereign
  [upstream-example]: https://github.com/al3x/sovereign/issues/322
  [bad-forking]: https://help.github.com/articles/why-are-my-contributions-not-showing-up-on-my-profile/#commit-was-made-in-a-fork

__HARD-HAT AREA!__

This project is a work-in-progress and is just lifting off the ground.

On the TODO is:

- Updating this README (e.g. replacing/fixing sovereign links to Empress)
- Closing [Issues](https://github.com/taoeffect/empress/issues).
- As much as is feasible making these playbooks "plug-n-play" and "swappable".
  I.e. make it simple for someone to choose Exim instead of Postfix, MySQL
  instead of Postgresql, etc.

Services Provided
-----------------

What do you get if you point this thing at a VPS? All kinds of good stuff!

-   [IMAP](https://en.wikipedia.org/wiki/Internet_Message_Access_Protocol) over
    TLS via [Dovecot](http://dovecot.org/), complete with full text search
    provided by [Solr](https://lucene.apache.org/solr/).
-   [POP3](https://en.wikipedia.org/wiki/Post_Office_Protocol) over TLS, also
    via Dovecot
-   [SMTP](https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol) over TLS
    via Postfix, including a nice set of
    [DNSBLs](https://en.wikipedia.org/wiki/DNSBL) to discard spam before it ever
    hits your filters.
-   Webmail via [Mailpile](http://www.mailpile.is/).
-   Virtual domains for your email, backed by [SQLite](https://www.sqlite.org/).
-   Spam fighting via [DSPAM](http://dspam.sourceforge.net/)
-   Mail server verification via [OpenDKIM](http://www.opendkim.org/), so folks
    know you’re legit.
-   Firewall management via [Uncomplicated Firewall
    (ufw)](https://wiki.ubuntu.com/UncomplicatedFirewall).
-   Intrusion prevention via [fail2ban](http://www.fail2ban.org/) and rootkit
    detection via [rkhunter](http://rkhunter.sourceforge.net).
-   SSH configuration preventing root login and insecure password authentication
-   Nightly backups to [Tarsnap](https://www.tarsnap.com/).
-   A bunch of nice-to-have tools like [mosh](http://mosh.mit.edu) and
    [htop](http://htop.sourceforge.net) that make life with a server a little
    easier.

No setup is perfect, but the general idea is to provide a bunch of useful
services while being reasonably secure and low-maintenance. Set it up, SSH in
every couple weeks, but mostly forget about it.

Don’t want one or more of the above services? Comment out the relevant role in
`site.yml`. Or get more granular and comment out the associated `include:`
directive in one of the playbooks.

Usage
=====

What You’ll Need
----------------

1.  A VPS (or bare-metal server if you wanna ball hard). My VPS is hosted at
    [RamNode](https://clientarea.ramnode.com/aff.php?aff=909).
    You’ll probably want at least 512 MB of RAM between nginx, Mailpile, Solr,
    and MariaDB (drop-in replacement for MySQL).
2.  [64-bit Debian 7](http://www.debian.org/) or an equivalent Linux
    distribution. (You can use whatever distro you want, but deviating from
    Debian will require more tweaks to the playbooks. See Ansible’s different
    [packaging](http://www.ansibleworks.com/docs/modules.html#packaging)
    modules.)
3.  A wildcard TLS certificate. We recommend self-signed certs or the free ones
    from [StartSSL](https://startssl.com).
4.  A [Tarsnap](http://www.tarsnap.com) account with some credit in it. You
    could comment this out if you want to use a different backup service.
    Consider paying your hosting provider for backups or using an additional
    backup service for redundancy.

Installation
------------

### 0. Clone the Repository

Make sure you have `git`, `python2`, `pip`, and `virtualenv` before starting.

    git clone git://github.com/taoeffect/empress.git
    cd empress
    virtualenv .env
    .env/bin/pip install -r requirements.txt

[Prior to 1.3, pip doesn't verify SSL certificates][ssl-verify], which impacts
Debian Wheezy, but will not impact Jessie. You may install an alternate version
of ansible (eg. from `wheezy-backports`) at your own risk.

  [ssl-verify]: http://pip.readthedocs.org/en/1.5.X/reference/pip_install.html#ssl-certificate-verification

### 1. Get a wildcard TLS certificate

Generate a private key and a certificate signing request (CSR):

    openssl req -nodes -newkey rsa:2048 -keyout roles/common/files/wildcard_private.key -out mycert.csr

Send your CSR to [StartSSL](https://startssl.com). They will give you
your signed public certificate. Place the certificate in
`roles/common/files/wildcard_public_cert.crt`.

Download your certificate authority’s combined cert to
`roles/common/files/wildcard_ca.pem`. You can also download the intermediate and
root certificates separately and concatenate them together in that order.

Lastly, test your certificate:

    openssl verify -verbose -CAfile roles/common/files/wildcard_ca.pem roles/common/files/wildcard_public_cert.crt

#### Self-signed TLS certificate

If you don't purchase or set up an existing certificate, empress will generate
one for you on the server.

Self-signed certs are free, easy, but are not yet authenticated by TLS (but [will be](https://github.com/okTurtles/dnschain)).

### 2. Get a Tarsnap machine key

If you haven’t already, [download and install
Tarsnap](https://www.tarsnap.com/download.html), or use `brew install tarsnap`
if you use [Homebrew](http://brew.sh).

Create a new machine key for your server:

    tarsnap-keygen --keyfile roles/tarsnap/files/decrypted_tarsnap.key --user me@example.com --machine example.com

### 3. Prep the server

For goodness sake, change the root password:

    passwd

Create a user account for Ansible to do its thing through:

    useradd deploy
    passwd deploy
    mkdir /home/deploy

Authorize your ssh key if you want passwordless ssh login (optional):

    mkdir /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    nano /home/deploy/.ssh/authorized_keys
    chmod 400 /home/deploy/.ssh/authorized_keys
    chown deploy:deploy /home/deploy -R

This account should be set up for passwordless sudo. Use `visudo` and add this
line:

    deploy  ALL=(ALL) NOPASSWD: ALL

### 4. Configure your installation

Modify the settings in `vars/user.yml` and `vars/mail.yml` to your liking (these two files will likely be combined).
If you want to see how they’re used in context, just search for the corresponding string.

Setting `password_hash` for your mail users is a bit tricky. You can generate
one using [doveadm-pw](http://wiki2.dovecot.org/Tools/Doveadm/Pw).

    # doveadm pw -s SHA512-CRYPT
    Enter new password: foo
    Retype new password: foo
    {SHA512-CRYPT}$6$drlIN9fx7Aj7/iLu$XvjeuQh5tlzNpNfs4NwxN7.HGRLglTKism0hxs2C1OvD02d3x8OBN9KQTueTr53nTJwVShtCYiW80SGXAjSyM0

Remove `{SHA512-CRYPT}` and insert the rest as the `password_hash` value.

Alternatively, if you don’t already have `doveadm` installed, Python 3.3 or
higher on Linux will generate the appropriate string for you (assuming your
password is `password`):

    python3 -c 'import crypt; print(crypt.crypt("password", salt=crypt.METHOD_SHA512))'

On OS X and other platforms the [passlib](https://pythonhosted.org/passlib/)
package may be used to generate the required string:

    python -c 'import passlib.hash; print(passlib.hash.sha512_crypt.encrypt("password", rounds=5000))'

Finally, replace the TODOs in the file `hosts`. If your SSH daemon listens on a
non-standard port, add a colon and the port number after the IP address.\
In that case you also need to add your custom port to the task
`Set firewall rules for web traffic and SSH` in the file
`roles/common/tasks/ufw.yml`.

### 5. Run the Ansible Playbooks

First, make sure you’ve [got Ansible 1.6+
installed](http://docs.ansible.com/intro_installation.html#getting-ansible).

To run the whole dang thing:

    ./setup_site.sh

To run just one or more piece, use tags. I try to tag all my includes for easy
isolated development. For example, to focus in on your firewall setup:

    ansible-playbook -i ./hosts --tags=ufw site.yml

You might find that it fails at one point or another. This is probably because
something needs to be done manually, usually because there’s no good way of
automating it. Fortunately, all the tasks are clearly named so you should be
able to find out where it stopped. I’ve tried to add comments where manual
intervention is necessary.

### 6. Set up DNS

If you’ve just bought a new domain name, point it at [Linode’s DNS
Manager](https://library.linode.com/dns-manager) or similar. Most VPS services
(and even some domain registrars) offer a managed DNS service that you can use
for this at no charge. If you’re using an existing domain that’s already managed
elsewhere, you can probably just modify a few records.

Create an `A` records which point to your server IP for:

- `example.com`
- `mail.example.com`
- `autoconfig.example.com` (for email client automatic configuration)

Create a `MX` record for `example.com` which assigns `mail.example.com` as the
domain’s mail server.

To ensure your emails pass DKIM checks you need to add a `txt` record. The name
field will be `default._domainkey.EXAMPLE.COM.` The value field contains the
public key used by OpenDKIM. The exact value needed can be found in the file
`/etc/opendkim/keys/EXAMPLE.COM/default.txt` it’ll look something like this:

    v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDKKAQfMwKVx+oJripQI+Ag4uTwYnsXKjgBGtl7Tk6UMTUwhMqnitqbR/ZQEZjcNolTkNDtyKZY2Z6LqvM4KsrITpiMbkV1eX6GKczT8Lws5KXn+6BHCKULGdireTAUr3Id7mtjLrbi/E3248Pq0Zs39hkDxsDcve12WccjafJVwIDAQAB

Set up SPF and reverse DNS [as per this
post](http://sealedabstract.com/code/nsa-proof-your-e-mail-in-2-hours/). Make
sure to validate that it’s all working, for example by sending an email to
<a href="mailto:check-auth@verifier.port25.com">check-auth@verifier.port25.com</a>
and reviewing the report that will be emailed back to you.

Troubleshooting
---------------

Create an issue.

Contributing
============

Fork me. Branch off of master. Do stuff. Send PR.

# Development

You can install sovereign to a VM with vagrant:

    virtualenv .env
    .env/bin/pip install -r requirements.txt
    PATH=".env/bin:$PATH" vagrant up

and to re-run ansible on the same machine:

    PATH=".env/bin:$PATH" vagrant provision

to run some automated tests, you can use:

    ./.env/bin/python -m unittests tests

License
-------

Original content is [GPLv3](http://gplv3.fsf.org), same as Ansible. All files
and templates based on third-party software should be considered under their
respective licenses.
