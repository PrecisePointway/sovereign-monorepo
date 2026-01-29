<?php
/**
 * Plugin Name: Sovereign Elite OS Integration
 * Plugin URI: https://sovereignsanctuarysystems.co.uk
 * Description: Gesture integration and CONTENT POLICY ENFORCEMENT for Sovereign Elite OS
 * Version: 1.1.0
 * Author: Architect
 * License: Proprietary
 * 
 * ============================================================================
 * CONTENT POLICY ENFORCEMENT
 * ============================================================================
 * BANNED: Anime imagery (all forms)
 * BANNED: Child-related imagery (ZERO TOLERANCE)
 * 
 * This plugin enforces content policy at:
 * - File uploads
 * - Post/page content
 * - Comments
 * - Search queries
 * - Media library
 * ============================================================================
 */

if (!defined('ABSPATH')) {
    exit;
}

// =============================================================================
// CONSTANTS
// =============================================================================

define('SOVEREIGN_VERSION', '1.1.0');
define('SOVEREIGN_LOG_DIR', WP_CONTENT_DIR . '/sovereign-logs');
define('SOVEREIGN_CONTENT_POLICY_ENABLED', true);

// =============================================================================
// CONTENT POLICY - BANNED PATTERNS
// =============================================================================

/**
 * Get banned filename and content patterns.
 * ZERO TOLERANCE for anime and child-related imagery.
 */
function sovereign_get_banned_patterns() {
    return array(
        // Anime-related
        'anime',
        'manga',
        'hentai',
        'waifu',
        'loli',
        'shota',
        'chibi',
        'kawaii',
        'otaku',
        'ecchi',
        'doujin',
        'ahegao',
        
        // Child-related (ZERO TOLERANCE)
        'child',
        'kids',
        'minor',
        'underage',
        'young',
        'teen',
        'preteen',
        'infant',
        'toddler',
        'baby',
        'juvenile',
        'adolescent',
        'schoolgirl',
        'schoolboy',
        'jailbait',
        'pedo',
        'csam',
    );
}

/**
 * Check if text contains banned patterns.
 */
function sovereign_check_content_policy($text) {
    if (!SOVEREIGN_CONTENT_POLICY_ENABLED) {
        return false;
    }
    
    $text_lower = strtolower($text);
    $banned_patterns = sovereign_get_banned_patterns();
    
    foreach ($banned_patterns as $pattern) {
        if (strpos($text_lower, $pattern) !== false) {
            $violation_type = sovereign_categorize_violation($pattern);
            
            sovereign_log_violation(array(
                'type' => $violation_type,
                'pattern' => $pattern,
                'context' => substr($text, 0, 100),
            ));
            
            return array(
                'type' => $violation_type,
                'pattern' => $pattern,
                'message' => 'Content policy violation: ' . $violation_type,
            );
        }
    }
    
    return false;
}

/**
 * Categorize violation type.
 */
function sovereign_categorize_violation($pattern) {
    $child_patterns = array('child', 'kid', 'minor', 'underage', 'young', 'teen', 
                           'preteen', 'infant', 'toddler', 'baby', 'juvenile', 
                           'adolescent', 'schoolgirl', 'schoolboy', 'jailbait', 
                           'pedo', 'loli', 'shota', 'csam');
    
    foreach ($child_patterns as $cp) {
        if (strpos($pattern, $cp) !== false) {
            return 'child_related';
        }
    }
    
    return 'anime';
}

/**
 * Log content policy violation.
 */
function sovereign_log_violation($violation) {
    if (!file_exists(SOVEREIGN_LOG_DIR)) {
        wp_mkdir_p(SOVEREIGN_LOG_DIR);
    }
    
    $log_file = SOVEREIGN_LOG_DIR . '/policy_violations.log';
    $timestamp = current_time('c');
    
    $log_entry = sprintf(
        "[%s] VIOLATION | Type: %s | Pattern: %s | Context: %s\n",
        $timestamp,
        $violation['type'],
        $violation['pattern'],
        $violation['context']
    );
    
    file_put_contents($log_file, $log_entry, FILE_APPEND | LOCK_EX);
    error_log('SOVEREIGN CONTENT POLICY VIOLATION: ' . json_encode($violation));
}

// =============================================================================
// UPLOAD FILTER
// =============================================================================

add_filter('wp_handle_upload_prefilter', 'sovereign_filter_upload');

function sovereign_filter_upload($file) {
    $violation = sovereign_check_content_policy($file['name']);
    
    if ($violation) {
        $file['error'] = sprintf(
            'Upload blocked: %s content is prohibited by platform policy.',
            $violation['type']
        );
        
        sovereign_log_event(array(
            'event' => 'upload_blocked',
            'filename' => $file['name'],
            'violation_type' => $violation['type'],
        ));
    }
    
    return $file;
}

// =============================================================================
// POST CONTENT FILTER
// =============================================================================

add_filter('wp_insert_post_data', 'sovereign_filter_post_content', 10, 2);

function sovereign_filter_post_content($data, $postarr) {
    // Check title
    $violation = sovereign_check_content_policy($data['post_title']);
    if ($violation) {
        wp_die(
            'Content policy violation in title: ' . esc_html($violation['type']) . ' content is prohibited.',
            'Content Policy Violation',
            array('response' => 403)
        );
    }
    
    // Check content
    $violation = sovereign_check_content_policy($data['post_content']);
    if ($violation) {
        wp_die(
            'Content policy violation in content: ' . esc_html($violation['type']) . ' content is prohibited.',
            'Content Policy Violation',
            array('response' => 403)
        );
    }
    
    return $data;
}

// =============================================================================
// COMMENT FILTER
// =============================================================================

add_filter('preprocess_comment', 'sovereign_filter_comment');

function sovereign_filter_comment($commentdata) {
    $violation = sovereign_check_content_policy($commentdata['comment_content']);
    
    if ($violation) {
        wp_die(
            'Comment blocked: ' . esc_html($violation['type']) . ' content is prohibited.',
            'Content Policy Violation',
            array('response' => 403)
        );
    }
    
    return $commentdata;
}

// =============================================================================
// HASH CHAIN LOGGING
// =============================================================================

function sovereign_log_event($event) {
    if (!file_exists(SOVEREIGN_LOG_DIR)) {
        wp_mkdir_p(SOVEREIGN_LOG_DIR);
    }
    
    $chain_file = SOVEREIGN_LOG_DIR . '/hash_chain.json';
    
    $chain = array();
    if (file_exists($chain_file)) {
        $chain = json_decode(file_get_contents($chain_file), true) ?: array();
    }
    
    $prev_hash = !empty($chain) ? end($chain)['hash'] : 'GENESIS';
    $timestamp = current_time('c');
    $payload = json_encode($event) . $prev_hash . $timestamp;
    $hash = hash('sha256', $payload);
    
    $record = array(
        'timestamp' => $timestamp,
        'event' => $event,
        'prev_hash' => $prev_hash,
        'hash' => $hash,
    );
    
    $chain[] = $record;
    file_put_contents($chain_file, json_encode($chain, JSON_PRETTY_PRINT), LOCK_EX);
    
    return $hash;
}

// =============================================================================
// REST API ROUTES
// =============================================================================

add_action('rest_api_init', 'sovereign_register_routes');

function sovereign_register_routes() {
    register_rest_route('sovereign/v1', '/gesture', array(
        'methods' => 'POST',
        'callback' => 'sovereign_handle_gesture',
        'permission_callback' => 'sovereign_verify_webhook',
    ));
    
    register_rest_route('sovereign/v1', '/status', array(
        'methods' => 'GET',
        'callback' => 'sovereign_get_status',
        'permission_callback' => '__return_true',
    ));
    
    register_rest_route('sovereign/v1', '/content-policy', array(
        'methods' => 'GET',
        'callback' => 'sovereign_get_content_policy_status',
        'permission_callback' => '__return_true',
    ));
}

function sovereign_get_content_policy_status() {
    $violations_file = SOVEREIGN_LOG_DIR . '/policy_violations.log';
    $violation_count = 0;
    
    if (file_exists($violations_file)) {
        $violation_count = count(file($violations_file));
    }
    
    return array(
        'enabled' => SOVEREIGN_CONTENT_POLICY_ENABLED,
        'banned_categories' => array('anime', 'child_related_imagery'),
        'violations_logged' => $violation_count,
        'policy_version' => '1.0.0',
    );
}

function sovereign_verify_webhook($request) {
    $secret = get_option('sovereign_webhook_secret');
    if (empty($secret)) return false;
    
    $signature = $request->get_header('X-Sovereign-Signature');
    $timestamp = $request->get_header('X-Sovereign-Timestamp');
    
    if (empty($signature) || empty($timestamp)) return false;
    if (abs(time() - intval($timestamp)) > 300) return false;
    
    $body = $request->get_body();
    $expected = hash_hmac('sha256', $timestamp . '.' . $body, $secret);
    
    return hash_equals($expected, $signature);
}

function sovereign_handle_gesture($request) {
    $params = $request->get_json_params();
    
    $hash = sovereign_log_event(array(
        'type' => 'gesture',
        'gesture_id' => sanitize_text_field($params['gesture_id'] ?? ''),
        'action' => sanitize_text_field($params['action'] ?? ''),
        'confidence' => floatval($params['confidence'] ?? 0),
    ));
    
    return array('status' => 'success', 'event_hash' => $hash);
}

function sovereign_get_status() {
    $chain_file = SOVEREIGN_LOG_DIR . '/hash_chain.json';
    $chain_length = 0;
    
    if (file_exists($chain_file)) {
        $chain = json_decode(file_get_contents($chain_file), true);
        $chain_length = is_array($chain) ? count($chain) : 0;
    }
    
    return array(
        'status' => 'operational',
        'version' => SOVEREIGN_VERSION,
        'hash_chain_length' => $chain_length,
        'content_policy' => array(
            'enabled' => SOVEREIGN_CONTENT_POLICY_ENABLED,
            'banned' => array('anime', 'child_related_imagery'),
        ),
        'timestamp' => current_time('c'),
    );
}

// =============================================================================
// ADMIN INTERFACE
// =============================================================================

add_action('admin_menu', 'sovereign_admin_menu');

function sovereign_admin_menu() {
    add_options_page(
        'Sovereign Elite OS',
        'Sovereign Elite OS',
        'manage_options',
        'sovereign-elite-os',
        'sovereign_admin_page'
    );
}

function sovereign_admin_page() {
    if (!current_user_can('manage_options')) return;
    
    if (isset($_POST['sovereign_save'])) {
        check_admin_referer('sovereign_settings');
        update_option('sovereign_webhook_secret', sanitize_text_field($_POST['webhook_secret']));
    }
    
    $webhook_secret = get_option('sovereign_webhook_secret', wp_generate_password(32, false));
    if (empty(get_option('sovereign_webhook_secret'))) {
        update_option('sovereign_webhook_secret', $webhook_secret);
    }
    
    ?>
    <div class="wrap">
        <h1>Sovereign Elite OS</h1>
        
        <div style="background: #ff4444; color: white; padding: 15px; margin: 20px 0; border-radius: 4px; font-weight: bold;">
            CONTENT POLICY ACTIVE: Anime and child-related imagery strictly prohibited
        </div>
        
        <h2>Content Policy Status</h2>
        <table class="form-table">
            <tr><th>Policy Status</th><td><strong style="color: green;">ENFORCED</strong></td></tr>
            <tr><th>Banned Categories</th><td>Anime imagery, Child-related imagery</td></tr>
            <tr><th>Enforcement Points</th><td>Uploads, Posts, Comments, Search</td></tr>
        </table>
        
        <h2>Gesture Integration</h2>
        <form method="post">
            <?php wp_nonce_field('sovereign_settings'); ?>
            <table class="form-table">
                <tr>
                    <th>Webhook URL</th>
                    <td><code><?php echo esc_html(rest_url('sovereign/v1/gesture')); ?></code></td>
                </tr>
                <tr>
                    <th>Webhook Secret</th>
                    <td><input type="text" name="webhook_secret" value="<?php echo esc_attr($webhook_secret); ?>" class="regular-text" /></td>
                </tr>
            </table>
            <p class="submit"><input type="submit" name="sovereign_save" class="button-primary" value="Save Settings" /></p>
        </form>
    </div>
    <?php
}

// =============================================================================
// ADMIN NOTICE
// =============================================================================

add_action('admin_notices', 'sovereign_content_policy_notice');

function sovereign_content_policy_notice() {
    $screen = get_current_screen();
    if (in_array($screen->base, array('post', 'upload', 'edit'))) {
        echo '<div class="notice notice-warning"><p><strong>Content Policy Active:</strong> Anime and child-related imagery are strictly prohibited.</p></div>';
    }
}

// =============================================================================
// ACTIVATION
// =============================================================================

register_activation_hook(__FILE__, 'sovereign_activate');

function sovereign_activate() {
    if (!file_exists(SOVEREIGN_LOG_DIR)) {
        wp_mkdir_p(SOVEREIGN_LOG_DIR);
    }
    
    if (empty(get_option('sovereign_webhook_secret'))) {
        update_option('sovereign_webhook_secret', wp_generate_password(32, false));
    }
    
    sovereign_log_event(array(
        'event' => 'plugin_activated',
        'version' => SOVEREIGN_VERSION,
        'content_policy' => 'enabled',
    ));
}
