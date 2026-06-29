from Core.config import settings
import requests


def send_critical_alert(order_id: str, error_details: str):
    """
    Sends a Discord alert when an order has exhausted all retry attempts.

    Purpose:
    Notify operations immediately so someone can manually investigate
    instead of silently losing an order.
    """

    # Read the webhook from our centralized configuration.
    # Never hardcode secrets inside the source code.
    webhook_url = settings.DISCORD_WEBHOOK_URL

    print(f"\n--- ATTEMPTING DISCORD PING FOR ORDER {order_id} ---")

    # Validate that a webhook actually exists before making
    # an HTTP request.
    if not webhook_url or not webhook_url.startswith("http"):
        print("ERROR: Discord webhook URL is missing or invalid.")
        return

    # Discord accepts JSON payloads.
    # "embeds" create rich formatted messages instead of plain text.
    payload = {
        "embeds": [
            {
                "title": "🚨 CRITICAL: Order Held For Review",

                "description":
                    "An order has exhausted all retry attempts and now "
                    "requires manual intervention.",

                # Decimal representation of Discord red.
                # Makes critical alerts visually obvious.
                "color": 16711680,

                "fields": [

                    {
                        "name": "Order ID",
                        "value": str(order_id),
                        "inline": True
                    },

                    {
                        "name": "Failure Reason",
                        "value": error_details,
                        "inline": False
                    }

                ]
            }
        ]
    }

    try:

        # Send the payload to Discord.
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10      # Prevent hanging forever if Discord is unreachable.
        )

        # Discord returns HTTP 204 on successful webhook delivery.
        if response.status_code == 204:
            print(f"SUCCESS: Discord alert sent for order {order_id}")

        else:
            print(
                f"ERROR: Discord rejected webhook "
                f"({response.status_code})"
            )

            # Discord usually returns a useful error body.
            print(response.text)

    except requests.RequestException as error:

        # Catch all network-related problems.
        # Examples:
        # - Internet unavailable
        # - Discord offline
        # - DNS failure
        # - Timeout
        print(f"NETWORK ERROR: Failed to send Discord alert.")
        print(error)

