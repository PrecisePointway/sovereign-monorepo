=== Sovereign Elite OS Integration ===
Contributors: architect
Tags: automation, webhook, gesture, api, sovereign
Requires at least: 6.0
Tested up to: 6.4
Stable tag: 1.0.0
Requires PHP: 8.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Gesture-driven content management and webhook integration for Sovereign Elite OS.

== Description ==

Sovereign Elite OS Integration connects your WordPress site to the Manus Pro gesture control system, enabling hands-free content management through physical gestures.

**Features:**

* Webhook endpoints for gesture events
* Hash-chained audit logging
* Gesture-triggered publishing
* Content snapshots
* REST API integration

**Endpoints:**

* `POST /wp-json/sovereign/v1/gesture` - Receive gesture events
* `GET /wp-json/sovereign/v1/status` - System status
* `POST /wp-json/sovereign/v1/publish` - Publish content
* `POST /wp-json/sovereign/v1/snapshot` - Create snapshot

== Installation ==

1. Upload the `sovereign-elite-os` folder to `/wp-content/plugins/`
2. Activate the plugin through the 'Plugins' menu
3. Configure settings under Settings > Sovereign Elite OS
4. Set your API key and webhook secret
5. Configure Manus Bridge to send events to your webhook URL

== Configuration ==

1. Go to Settings > Sovereign Elite OS
2. Enter your API Key (from Manus Bridge)
3. Note the auto-generated Webhook Secret
4. Copy the Gesture Webhook URL to your Manus Bridge config
5. Enable Hash Chain Logging for audit compliance

== Changelog ==

= 1.0.0 =
* Initial release
* Gesture webhook endpoint
* Hash-chained event logging
* Gesture-triggered publishing
* Content snapshots
