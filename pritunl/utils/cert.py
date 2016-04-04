from pritunl.constants import *
from pritunl.utils.misc import check_output_logged, get_temp_path
from pritunl import settings

import os
import collections

def create_server_cert():
    from pritunl import acme
    from pritunl import logger

    logger.info('Generating server certificate...', 'utils')

    if settings.app.acme_domain:
        acme.update_acme_cert()
        return

    server_cert_path = os.path.join(settings.conf.temp_path, SERVER_CERT_NAME)
    server_key_path = os.path.join(settings.conf.temp_path, SERVER_KEY_NAME)

    generate_server_cert(server_cert_path, server_key_path)

    with open(server_cert_path, 'r') as server_cert_file:
        settings.app.server_cert = server_cert_file.read().strip()
    with open(server_key_path, 'r') as server_key_file:
        settings.app.server_key = server_key_file.read().strip()

def write_server_cert():
    server_cert_path = os.path.join(settings.conf.temp_path, SERVER_CERT_NAME)
    server_chain_path = os.path.join(settings.conf.temp_path,
        SERVER_CHAIN_NAME)
    server_key_path = os.path.join(settings.conf.temp_path, SERVER_KEY_NAME)

    server_cert_full = settings.app.server_cert

    if settings.app.acme_domain:
        server_cert_full += LETS_ENCRYPT_INTER

    server_cert_full = server_cert_full.strip()
    server_cert_full = server_cert_full.split('-----BEGIN CERTIFICATE-----')

    server_certs = collections.deque()

    for cert in server_cert_full:
        cert = cert.strip()
        if not cert:
            continue

        server_certs.append('-----BEGIN CERTIFICATE-----\n' + cert)

    server_cert = server_certs.popleft()
    server_chain = '\n'.join(server_certs)

    with open(server_cert_path, 'w') as server_cert_file:
        server_cert_file.write(server_cert)
    with open(server_chain_path, 'w') as server_chain_file:
        server_chain_file.write(server_chain)
    with open(server_key_path, 'w') as server_key_file:
        os.chmod(server_key_path, 0600)
        server_key_file.write(settings.app.server_key)

def generate_server_cert(server_cert_path, server_key_path):
    check_output_logged([
        'openssl', 'req', '-batch', '-x509', '-nodes', '-sha256',
        '-newkey', 'rsa:4096',
        '-days', '3652',
        '-keyout', server_key_path,
        '-out', server_cert_path,
    ])
    os.chmod(server_key_path, 0600)

def generate_private_key():
    return check_output_logged([
        'openssl', 'genrsa', '4096',
    ])

def generate_csr(private_key, domain):
    private_key_path = get_temp_path() + '.key'

    with open(private_key_path, 'w') as private_key_file:
        os.chmod(private_key_path, 0600)
        private_key_file.write(private_key)

    csr = check_output_logged([
        'openssl',
        'req',
        '-new',
        '-sha256',
        '-key', private_key_path,
        '-subj', '/CN=%s' % domain,
    ])

    try:
        os.remove(private_key_path)
    except:
        pass

    return csr
