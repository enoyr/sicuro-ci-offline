"""Build from the internal registry only; support existing Podman and Docker runners."""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from site_config import load, default_path, image_prefix


def build():
    c = load(default_path(), os.environ['CI_COMMIT_BRANCH'])
    for key in ['http_proxy', 'https_proxy', 'no_proxy']:
        os.environ[key] = c.get(key, '')
        os.environ[key.upper()] = c.get(key, '')
    prefix = image_prefix(c)
    base = prefix + '/runtime/younity-web-portable@sha256:f32534b8f34707005fff6dc376c43c633692ef9f5043ace49cef5304b1516e89'
    image = prefix + '/web:' + os.environ['CI_COMMIT_SHA']
    engine = os.environ.get('SICURO_BUILD_ENGINE', 'podman')
    if engine not in ('docker', 'podman'):
        raise ValueError('SICURO_BUILD_ENGINE deve essere docker oppure podman')
    auth_file = os.environ.get('SICURO_BUILD_AUTH')
    if auth_file:
        auth = json.loads(Path(auth_file).read_text())
        user, password = auth['username'], auth['password']
    else:
        if c['registry'] != os.environ.get('CI_REGISTRY'):
            raise ValueError('Configurare SICURO_BUILD_AUTH con le credenziali Harbor')
        user, password = os.environ['CI_REGISTRY_USER'], os.environ['CI_REGISTRY_PASSWORD']
    Path('image-digest.txt').unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        if engine == 'podman':
            auth_path = tmp + '/auth.json'
            subprocess.run(['podman', 'login', '--authfile', auth_path, '--username', user, '--password-stdin', c['registry']], input=password, text=True, check=True)
            subprocess.run(['podman', 'pull', '--authfile', auth_path, base], check=True)
            subprocess.run(['podman', 'build', '--network=none', '--pull=never', '--jobs=1', '--build-arg', 'BASE_IMAGE=' + base, '-f', 'docker/web/Dockerfile', '-t', image, '.'], check=True)
            subprocess.run(['podman', 'push', '--authfile', auth_path, '--digestfile', 'image-digest.txt', image], check=True)
        else:
            # Ephemeral auth: never write registry credentials into the checkout.
            env = {**os.environ, 'DOCKER_CONFIG': tmp, 'DOCKER_BUILDKIT': '1'}
            cli = ['docker', '--config', tmp]
            subprocess.run(cli + ['version', '--format', '{{.Server.Version}}'], env=env, check=True)
            subprocess.run(cli + ['login', '--username', user, '--password-stdin', c['registry']], input=password, text=True, env=env, check=True)
            subprocess.run(cli + ['pull', base], env=env, check=True)
            subprocess.run(cli + ['build', '--network=none', '--pull=false', '--build-arg', 'BASE_IMAGE=' + base, '-f', 'docker/web/Dockerfile', '-t', image, '.'], env=env, check=True)
            subprocess.run(cli + ['push', image], env=env, check=True)
            result = subprocess.run(cli + ['image', 'inspect', '--format', '{{json .RepoDigests}}', image], env=env, capture_output=True, text=True, check=True)
            repository = image.rsplit(':', 1)[0]
            digests = {ref.split('@', 1)[1] for ref in json.loads(result.stdout) or [] if ref.startswith(repository + '@')}
            if len(digests) != 1:
                raise ValueError('Digest pubblicato non univoco per ' + repository)
            digest = digests.pop()
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
                raise ValueError('Digest registry non valido')
            Path('image-digest.txt').write_text(digest + '\n')
    digest = Path('image-digest.txt').read_text().strip()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError('Digest finale non valido')


if __name__ == '__main__':
    build()
