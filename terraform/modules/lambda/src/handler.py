import json
import logging
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    processed = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        size = record["s3"]["object"].get("size", 0)
        parts = key.split("/")
        ticket_id = parts[1] if len(parts) > 2 else None

        logger.info(json.dumps({
            "message": "attachment_received",
            "event_name": record.get("eventName"),
            "bucket": bucket,
            "key": key,
            "ticket_id": ticket_id,
            "size_bytes": size,
        }))
        processed.append(key)

    return {"processed": len(processed)}
