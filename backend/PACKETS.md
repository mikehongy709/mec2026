# Optional mission packet validation

This is a separate backend ingestion path matching the group's simulator packet
format. It does not change the frontend, its simulation, or the existing
`/api/telemetry` and dashboard endpoints. The frontend does not call this endpoint
yet; the teammate handling integration can connect it when ready.

Start the existing `app.main:app` backend normally. Startup creates a new
`mission_packets` table without altering the existing mission tables.

## Send a packet

`POST /api/packet-streams/{stream_id}/packets`

Choose a new stream ID for each simulator run, including after a sequence reset.
Keep that ID and the original sequence numbers during dropouts and replay.
Different phases within the same run share one stream. Stream IDs are 1-64 ASCII
letters, digits, `_` or `-`, starting with a letter or digit; a UUID works.

Example request using PowerShell:

```powershell
$packetBody = '{"alt":0,"vel":0,"g":1,"tmp":24,"pwr":98,"prs":310,"seq":1,"crc":4421}'
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/packet-streams/demo-run-1/packets" -ContentType "application/json" -Body $packetBody
```

The JSON body is the group's flat packet, without a `readings` wrapper:

```json
{"alt":0,"vel":0,"g":1,"tmp":24,"pwr":98,"prs":310,"seq":1,"crc":4421}
```

| Result | HTTP status | Behavior |
| --- | --- | --- |
| New valid packet | 201 | Stored once; receipt has `duplicate: false` |
| Exact replay | 200 | Original ID/time returned with `duplicate: true`; no new row |
| Same stream/sequence, different valid data | 409 | Original packet retained |
| Bad checksum, missing/unknown fields, invalid values | 422 | Nothing stored |

Each receipt includes `id`, `stream_id`, `seq`, `recorded_at` and `duplicate`.
Duplicate protection is enforced by a database unique constraint, including
simultaneous requests, and survives backend restarts. Out-of-order packets are
accepted; an older sequence is not automatically a duplicate.

## Validation rules

- All six readings (`alt`, `vel`, `g`, `tmp`, `pwr`, `prs`) must be finite JSON
  numbers, not strings or booleans. No extra fields are accepted.
- Altitude, velocity and pressure cannot be negative. Battery is 0-100.
  Signed G-load and negative temperature are allowed. Ordinary alert threshold
  violations are retained as evidence, not discarded as corrupt packets.
- `seq` is a nonnegative integer within JavaScript's safe integer range.
- `crc` follows the exact browser formula, including JavaScript rounding and
  signed remainder:

  ```js
  Math.round(alt*10 + vel*1000 + g*100 + tmp*10 + pwr*10 + prs*10 + seq) % 65521
  ```

  The weighted sum must also remain within JavaScript's safe integer range.

This checksum detects accidental corruption; it is not sender authentication.
Accepted packets remain in their own archive. They do not feed the older
dashboard's differently shaped readings or implement a WebSocket transport.

## Checks

From `backend`, install `requirements-dev.txt`, then run:

```sh
python -m unittest discover -s tests -v
```

Packet endpoint tests use temporary SQLite files and guard against accessing the
shared demo database. They cover browser checksum examples, invalid packets,
replay, run separation, concurrent requests, restart persistence, and compatibility
with the existing mission API.
