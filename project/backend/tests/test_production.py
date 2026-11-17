"""Synthetic checks for the same-origin production server boundary."""
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.production import mount_frontend


def test_built_frontend_and_api_share_origin_without_exposing_private_files(tmp_path):
    public=tmp_path/'dist';public.mkdir()
    (public/'index.html').write_text('<html>Synthetic frontend</html>')
    (public/'asset.js').write_text('/* Synthetic asset */')
    private=tmp_path/'private';private.mkdir()
    (private/'secret.txt').write_text('Synthetic private fixture')
    (public/'private-link.txt').symlink_to(private/'secret.txt')
    app=mount_frontend(create_app(tmp_path/'data',admin_token='synthetic-test-token'),public)
    with TestClient(app) as client:
        assert client.get('/').text=='<html>Synthetic frontend</html>'
        assert client.get('/asset.js').status_code==200
        assert client.get('/api/health').json()['backend']=='ok'
        assert client.get('/api/proverbs').status_code==200
        assert client.get('/api/admin/proverbs').status_code in (401,404)
        for path in ['/.env','/data/admin-token','/data/gaade.db','/models/whisper/config.json','/private-link.txt','/api/not-an-endpoint','/../private/secret.txt']:
            assert client.get(path).status_code==404
