async def test_ready(cli):
    resp = await cli.get('/healthz/ready')
    assert resp.status_code == 200
