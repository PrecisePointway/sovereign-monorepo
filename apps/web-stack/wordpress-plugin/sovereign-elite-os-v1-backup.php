<?php
/**
 * Plugin Name: Sovereign Elite OS Integration
 * Plugin URI: https://sovereignsanctuarysystems.co.uk
 * Description: Gesture-driven content management and webhook integration for Sovereign Elite OS
 * Version: 1.0.0
 * Author: Architect
 * Author URI: https://sovereignsanctuarysystems.co.uk
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: sovereign-elite-os
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Plugin constants
define('SOVEREIGN_VERSION', '1.0.0');
define('SOVEREIGN_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('SOVEREIGN_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Main plugin class
 */
class Sovereign_Elite_OS {
    
    private static $instance = null;
    private $api_key;
    private $webhook_secret;
    
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        $this->api_key = get_option('sovereign_api_key', '');
        $this->webhook_secret = get_option('sovereign_webhook_secret', '');
        
        add_action('init', array($this, 'init'));
        add_action('admin_menu', array($this, 'admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
        add_action('rest_api_init', array($this, 'register_rest_routes'));
        
        // Gesture-triggered actions
        add_action('sovereign_gesture_publish', array($this, 'handle_gesture_publish'), 10, 2);
        add_action('sovereign_gesture_snapshot', array($this, 'handle_gesture_snapshot'), 10, 2);
    }
    
    public function init() {
        // Register custom post status for gesture-queued content
        register_post_status('gesture_queued', array(
            'label' => _x('Gesture Queued', 'post status', 'sovereign-elite-os'),
            'public' => false,
            'internal' => true,
            'show_in_admin_all_list' => true,
            'show_in_admin_status_list' => true,
            'label_count' => _n_noop('Gesture Queued <span class="count">(%s)</span>', 'Gesture Queued <span class="count">(%s)</span>', 'sovereign-elite-os'),
        ));
    }
    
    /**
     * Admin menu
     */
    public function admin_menu() {
        add_options_page(
            'Sovereign Elite OS',
            'Sovereign Elite OS',
            'manage_options',
            'sovereign-elite-os',
            array($this, 'settings_page')
        );
    }
    
    /**
     * Register settings
     */
    public function register_settings() {
        register_setting('sovereign_settings', 'sovereign_api_key');
        register_setting('sovereign_settings', 'sovereign_webhook_secret');
        register_setting('sovereign_settings', 'sovereign_manus_bridge_url');
        register_setting('sovereign_settings', 'sovereign_hash_chain_enabled');
        register_setting('sovereign_settings', 'sovereign_audit_log_enabled');
    }
    
    /**
     * Settings page
     */
    public function settings_page() {
        ?>
        <div class="wrap">
            <h1>Sovereign Elite OS Integration</h1>
            
            <form method="post" action="options.php">
                <?php settings_fields('sovereign_settings'); ?>
                
                <h2>API Configuration</h2>
                <table class="form-table">
                    <tr>
                        <th scope="row">API Key</th>
                        <td>
                            <input type="password" name="sovereign_api_key" 
                                   value="<?php echo esc_attr(get_option('sovereign_api_key')); ?>" 
                                   class="regular-text" />
                            <p class="description">Authentication key for Manus Bridge API calls</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Webhook Secret</th>
                        <td>
                            <input type="password" name="sovereign_webhook_secret" 
                                   value="<?php echo esc_attr(get_option('sovereign_webhook_secret')); ?>" 
                                   class="regular-text" />
                            <p class="description">HMAC secret for webhook signature verification</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Manus Bridge URL</th>
                        <td>
                            <input type="url" name="sovereign_manus_bridge_url" 
                                   value="<?php echo esc_attr(get_option('sovereign_manus_bridge_url', 'http://localhost:8765')); ?>" 
                                   class="regular-text" />
                            <p class="description">WebSocket URL for Manus Bridge connection</p>
                        </td>
                    </tr>
                </table>
                
                <h2>Security Settings</h2>
                <table class="form-table">
                    <tr>
                        <th scope="row">Hash Chain Logging</th>
                        <td>
                            <label>
                                <input type="checkbox" name="sovereign_hash_chain_enabled" value="1" 
                                       <?php checked(get_option('sovereign_hash_chain_enabled'), 1); ?> />
                                Enable cryptographic hash chain for all actions
                            </label>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Audit Logging</th>
                        <td>
                            <label>
                                <input type="checkbox" name="sovereign_audit_log_enabled" value="1" 
                                       <?php checked(get_option('sovereign_audit_log_enabled'), 1); ?> />
                                Enable detailed audit logging
                            </label>
                        </td>
                    </tr>
                </table>
                
                <h2>Webhook Endpoints</h2>
                <table class="form-table">
                    <tr>
                        <th scope="row">Gesture Webhook</th>
                        <td>
                            <code><?php echo esc_url(rest_url('sovereign/v1/gesture')); ?></code>
                            <p class="description">POST endpoint for gesture events from Manus Bridge</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Status Endpoint</th>
                        <td>
                            <code><?php echo esc_url(rest_url('sovereign/v1/status')); ?></code>
                            <p class="description">GET endpoint for system status</p>
                        </td>
                    </tr>
                </table>
                
                <?php submit_button(); ?>
            </form>
            
            <h2>Recent Gesture Events</h2>
            <?php $this->display_recent_events(); ?>
        </div>
        <?php
    }
    
    /**
     * Display recent gesture events
     */
    private function display_recent_events() {
        $events = get_option('sovereign_gesture_events', array());
        $events = array_slice($events, -10); // Last 10 events
        
        if (empty($events)) {
            echo '<p>No gesture events recorded yet.</p>';
            return;
        }
        
        echo '<table class="wp-list-table widefat fixed striped">';
        echo '<thead><tr><th>Time</th><th>Gesture</th><th>Action</th><th>Status</th><th>Hash</th></tr></thead>';
        echo '<tbody>';
        
        foreach (array_reverse($events) as $event) {
            printf(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><code>%s</code></td></tr>',
                esc_html($event['timestamp']),
                esc_html($event['gesture_id']),
                esc_html($event['action']),
                esc_html($event['status']),
                esc_html(substr($event['hash'], 0, 12) . '...')
            );
        }
        
        echo '</tbody></table>';
    }
    
    /**
     * Register REST API routes
     */
    public function register_rest_routes() {
        // Gesture webhook endpoint
        register_rest_route('sovereign/v1', '/gesture', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_gesture_webhook'),
            'permission_callback' => array($this, 'verify_webhook_signature'),
        ));
        
        // Status endpoint
        register_rest_route('sovereign/v1', '/status', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_status'),
            'permission_callback' => '__return_true',
        ));
        
        // Publish endpoint (gesture-triggered)
        register_rest_route('sovereign/v1', '/publish', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_publish'),
            'permission_callback' => array($this, 'verify_webhook_signature'),
        ));
        
        // Snapshot endpoint
        register_rest_route('sovereign/v1', '/snapshot', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_snapshot'),
            'permission_callback' => array($this, 'verify_webhook_signature'),
        ));
    }
    
    /**
     * Verify webhook signature
     */
    public function verify_webhook_signature($request) {
        $signature = $request->get_header('X-Sovereign-Signature');
        $timestamp = $request->get_header('X-Sovereign-Timestamp');
        $body = $request->get_body();
        
        if (empty($signature) || empty($timestamp)) {
            return false;
        }
        
        // Check timestamp freshness (5 minute window)
        if (abs(time() - intval($timestamp)) > 300) {
            return false;
        }
        
        // Verify HMAC signature
        $expected = hash_hmac('sha256', $timestamp . '.' . $body, $this->webhook_secret);
        
        return hash_equals($expected, $signature);
    }
    
    /**
     * Handle gesture webhook
     */
    public function handle_gesture_webhook($request) {
        $params = $request->get_json_params();
        
        $gesture_id = sanitize_text_field($params['gesture_id'] ?? '');
        $action = sanitize_text_field($params['action'] ?? '');
        $confidence = floatval($params['confidence'] ?? 0);
        $biometric_hash = sanitize_text_field($params['biometric_hash'] ?? '');
        
        // Log event
        $event = array(
            'timestamp' => current_time('mysql'),
            'gesture_id' => $gesture_id,
            'action' => $action,
            'confidence' => $confidence,
            'status' => 'received',
            'hash' => $this->generate_event_hash($params),
        );
        
        $this->log_event($event);
        
        // Route to appropriate handler
        switch ($action) {
            case 'publish':
                do_action('sovereign_gesture_publish', $params, $event);
                break;
            case 'snapshot':
                do_action('sovereign_gesture_snapshot', $params, $event);
                break;
            default:
                return new WP_REST_Response(array(
                    'status' => 'error',
                    'message' => 'Unknown action: ' . $action,
                ), 400);
        }
        
        return new WP_REST_Response(array(
            'status' => 'success',
            'event_hash' => $event['hash'],
        ), 200);
    }
    
    /**
     * Handle gesture-triggered publish
     */
    public function handle_gesture_publish($params, $event) {
        // Publish all queued posts
        $queued_posts = get_posts(array(
            'post_status' => 'gesture_queued',
            'numberposts' => -1,
        ));
        
        foreach ($queued_posts as $post) {
            wp_update_post(array(
                'ID' => $post->ID,
                'post_status' => 'publish',
            ));
            
            // Log individual publish
            $this->log_event(array(
                'timestamp' => current_time('mysql'),
                'gesture_id' => $params['gesture_id'],
                'action' => 'post_published',
                'status' => 'success',
                'post_id' => $post->ID,
                'hash' => $this->generate_event_hash(array('post_id' => $post->ID)),
            ));
        }
        
        return count($queued_posts);
    }
    
    /**
     * Handle gesture-triggered snapshot
     */
    public function handle_gesture_snapshot($params, $event) {
        // Create content snapshot
        $snapshot = array(
            'timestamp' => current_time('mysql'),
            'posts' => wp_count_posts(),
            'pages' => wp_count_posts('page'),
            'users' => count_users(),
            'plugins' => get_plugins(),
            'theme' => wp_get_theme()->get('Name'),
        );
        
        $snapshot_hash = hash('sha256', json_encode($snapshot));
        
        // Store snapshot
        $snapshots = get_option('sovereign_snapshots', array());
        $snapshots[] = array(
            'hash' => $snapshot_hash,
            'data' => $snapshot,
            'triggered_by' => $params['gesture_id'],
        );
        update_option('sovereign_snapshots', array_slice($snapshots, -50));
        
        return $snapshot_hash;
    }
    
    /**
     * Get system status
     */
    public function get_status($request) {
        return new WP_REST_Response(array(
            'status' => 'operational',
            'version' => SOVEREIGN_VERSION,
            'wordpress_version' => get_bloginfo('version'),
            'hash_chain_enabled' => (bool) get_option('sovereign_hash_chain_enabled'),
            'audit_log_enabled' => (bool) get_option('sovereign_audit_log_enabled'),
            'last_gesture_event' => $this->get_last_event(),
            'timestamp' => current_time('c'),
        ), 200);
    }
    
    /**
     * Handle publish endpoint
     */
    public function handle_publish($request) {
        $params = $request->get_json_params();
        $post_id = intval($params['post_id'] ?? 0);
        
        if ($post_id) {
            wp_update_post(array(
                'ID' => $post_id,
                'post_status' => 'publish',
            ));
            
            return new WP_REST_Response(array(
                'status' => 'success',
                'post_id' => $post_id,
            ), 200);
        }
        
        return new WP_REST_Response(array(
            'status' => 'error',
            'message' => 'No post_id provided',
        ), 400);
    }
    
    /**
     * Handle snapshot endpoint
     */
    public function handle_snapshot($request) {
        $hash = $this->handle_gesture_snapshot(
            array('gesture_id' => 'api_call'),
            array()
        );
        
        return new WP_REST_Response(array(
            'status' => 'success',
            'snapshot_hash' => $hash,
        ), 200);
    }
    
    /**
     * Generate event hash
     */
    private function generate_event_hash($data) {
        $last_hash = $this->get_last_hash();
        $payload = json_encode($data) . $last_hash . microtime(true);
        return hash('sha256', $payload);
    }
    
    /**
     * Get last hash from chain
     */
    private function get_last_hash() {
        $events = get_option('sovereign_gesture_events', array());
        if (empty($events)) {
            return 'GENESIS';
        }
        return end($events)['hash'];
    }
    
    /**
     * Get last event
     */
    private function get_last_event() {
        $events = get_option('sovereign_gesture_events', array());
        return empty($events) ? null : end($events);
    }
    
    /**
     * Log event
     */
    private function log_event($event) {
        $events = get_option('sovereign_gesture_events', array());
        $events[] = $event;
        update_option('sovereign_gesture_events', array_slice($events, -100));
    }
}

// Initialize plugin
Sovereign_Elite_OS::get_instance();

// Activation hook
register_activation_hook(__FILE__, function() {
    // Generate default webhook secret if not set
    if (!get_option('sovereign_webhook_secret')) {
        update_option('sovereign_webhook_secret', wp_generate_password(32, false));
    }
    
    // Enable hash chain by default
    if (!get_option('sovereign_hash_chain_enabled')) {
        update_option('sovereign_hash_chain_enabled', 1);
    }
    
    // Flush rewrite rules
    flush_rewrite_rules();
});

// Deactivation hook
register_deactivation_hook(__FILE__, function() {
    flush_rewrite_rules();
});
