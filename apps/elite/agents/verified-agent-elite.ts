/**
 * Verified Agent Elite - Sovereign Sanctuary
 * Cryptographic PR review agent with audit trail and verification gates.
 *
 * Version: 2.0.0 (Bug-fixed and cleaned)
 * Author: Manus AI for Architect
 *
 * Changes from v1:
 * - Fixed HMAC signature generation (was using wrong crypto method)
 * - Added proper error types and handling
 * - Fixed token estimation for accurate cost tracking
 * - Added retry logic for API calls
 * - Improved type safety throughout
 * - Added configuration validation
 * - Fixed potential null reference issues
 */

import { generateObject } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';
import crypto from 'crypto';
import dotenv from 'dotenv';

dotenv.config();

// ═══════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════

interface AgentConfig {
  agentId: string;
  signingKey: string;
  model: string;
  maxDiffSize: number;
  maxRetries: number;
  retryDelayMs: number;
}

const config: AgentConfig = {
  agentId: process.env.AGENT_ID ?? 'agent-pr-reviewer-v2',
  signingKey: process.env.AGENT_SIGNING_KEY ?? 'dev-key-do-not-use-in-prod',
  model: process.env.OPENAI_MODEL ?? 'gpt-4o',
  maxDiffSize: 100_000,
  maxRetries: 3,
  retryDelayMs: 1000,
};

// Validate configuration
if (config.signingKey === 'dev-key-do-not-use-in-prod') {
  console.warn('⚠️  WARNING: Using default signing key. Set AGENT_SIGNING_KEY in production.');
}

// ═══════════════════════════════════════════════════════════════════
// SCHEMAS
// ═══════════════════════════════════════════════════════════════════

const OutputSchema = z.object({
  analysis: z.string().max(600),
  confidenceScore: z.number().min(0).max(1),
  proposedAction: z.enum(['APPROVE', 'REQUEST_CHANGES', 'ESCALATE']),

  structuredData: z.object({
    reviewId: z.string(),
    overallRisk: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    riskScore: z.number().int().min(0).max(100),
    categories: z
      .array(z.enum(['SECURITY', 'RELIABILITY', 'PERFORMANCE', 'TESTS', 'DX', 'DOCS']))
      .max(4),

    keyFindings: z
      .array(
        z.object({
          id: z.string(),
          severity: z.enum(['INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
          filePath: z.string(),
          lineStart: z.number().int().min(1),
          lineEnd: z.number().int().min(1),
          message: z.string().max(240),
          evidence: z.string().max(240),
        })
      )
      .max(8),

    requiredActions: z
      .array(
        z.object({
          type: z.enum([
            'NONE',
            'ADD_TESTS',
            'FIX_BUG',
            'SECURITY_REVIEW',
            'UPDATE_DOCS',
            'ADD_VALIDATION',
            'ADD_LOGGING',
            'PERF_CHECK',
            'ROLLBACK_PLAN',
          ]),
          description: z.string().max(240),
        })
      )
      .max(6),

    approvalChecklist: z.array(z.string().max(120)).min(1).max(6),
    suggestedReviewers: z
      .array(
        z.object({
          role: z.enum(['CODEOWNER', 'SECURITY', 'SRE', 'DOMAIN_EXPERT']),
          reason: z.string().max(140),
        })
      )
      .max(3),

    summaryForPRComment: z.string().max(500),
    filesTouched: z
      .array(
        z.object({
          path: z.string(),
          changeType: z.enum(['ADDED', 'MODIFIED', 'DELETED', 'RENAMED', 'UNKNOWN']),
          riskNotes: z.string().max(140),
        })
      )
      .max(25),
  }),
});

type Output = z.infer<typeof OutputSchema>;

// ═══════════════════════════════════════════════════════════════════
// AUDIT TRAIL TYPES
// ═══════════════════════════════════════════════════════════════════

interface AuditTrail {
  reviewId: string;
  agentId: string;
  agentVersion: string;
  timestamp: string;
  inputHash: string;
  outputSignature: string;
  tokensUsed: number;
  costUSD: number;
  modelUsed: string;
  verificationGateDecision: 'PASS' | 'FAIL';
  verificationReason?: string;
}

interface SignedReview {
  structuredData: Output['structuredData'];
  auditTrail: AuditTrail;
  signature: string;
}

// ═══════════════════════════════════════════════════════════════════
// CRYPTOGRAPHIC FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

/**
 * Hash the input diff using SHA-256.
 * Used to detect tampering of the input.
 */
function hashInput(input: string): string {
  return crypto.createHash('sha256').update(input, 'utf8').digest('hex');
}

/**
 * Sign the review output using HMAC-SHA256.
 * BUG FIX: Changed from incorrect crypto.hmac to crypto.createHmac
 */
function signReview(
  structuredData: Output['structuredData'],
  auditTrail: Omit<AuditTrail, 'outputSignature'>
): string {
  const payload = JSON.stringify({ structuredData, auditTrail }, null, 0);
  return crypto.createHmac('sha256', config.signingKey).update(payload, 'utf8').digest('hex');
}

/**
 * Verify a signed review.
 * Uses timing-safe comparison to prevent timing attacks.
 */
function verifySignature(review: SignedReview): boolean {
  const { outputSignature, ...auditTrailWithoutSig } = review.auditTrail;
  const recomputed = signReview(review.structuredData, auditTrailWithoutSig);

  // Ensure both buffers are the same length before comparison
  const sigBuffer = Buffer.from(review.signature, 'hex');
  const recomputedBuffer = Buffer.from(recomputed, 'hex');

  if (sigBuffer.length !== recomputedBuffer.length) {
    return false;
  }

  return crypto.timingSafeEqual(sigBuffer, recomputedBuffer);
}

// ═══════════════════════════════════════════════════════════════════
// TOKEN AND COST ESTIMATION
// ═══════════════════════════════════════════════════════════════════

/**
 * Estimate token count from text.
 * BUG FIX: Improved estimation using GPT tokenization heuristics.
 */
function estimateTokens(text: string): number {
  // GPT models use ~4 characters per token on average for English
  // But code tends to be more token-dense
  const charCount = text.length;
  const wordCount = text.split(/\s+/).length;

  // Use a weighted average of character and word-based estimates
  const charBasedEstimate = Math.ceil(charCount / 4);
  const wordBasedEstimate = Math.ceil(wordCount * 1.3);

  return Math.max(charBasedEstimate, wordBasedEstimate);
}

/**
 * Calculate cost based on token usage.
 * Pricing as of 2025 (update as needed).
 */
function calculateCost(inputTokens: number, outputTokens: number, model: string): number {
  // GPT-4o pricing (per 1K tokens)
  const pricing: Record<string, { input: number; output: number }> = {
    'gpt-4o': { input: 0.005, output: 0.015 },
    'gpt-4o-mini': { input: 0.00015, output: 0.0006 },
    'gpt-4-turbo': { input: 0.01, output: 0.03 },
  };

  const rates = pricing[model] ?? pricing['gpt-4o'];
  return (inputTokens / 1000) * rates.input + (outputTokens / 1000) * rates.output;
}

// ═══════════════════════════════════════════════════════════════════
// VERIFICATION GATE
// ═══════════════════════════════════════════════════════════════════

interface VerificationResult {
  passed: boolean;
  reason?: string;
}

/**
 * Verification gate to ensure output quality.
 * Returns detailed reason if verification fails.
 */
function verifyOutput(result: Output): VerificationResult {
  // Check confidence threshold
  if (result.confidenceScore < 0.9) {
    return { passed: false, reason: `Low confidence score: ${result.confidenceScore}` };
  }

  // Check for escalation
  if (result.proposedAction === 'ESCALATE') {
    return { passed: false, reason: 'Agent requested escalation' };
  }

  const r = result.structuredData;

  // Check risk level
  if (r.overallRisk === 'CRITICAL') {
    return { passed: false, reason: 'Critical risk level detected' };
  }

  if (r.riskScore >= 75) {
    return { passed: false, reason: `High risk score: ${r.riskScore}` };
  }

  // Validate key findings have evidence
  for (const finding of r.keyFindings) {
    if (!finding.evidence || finding.evidence.trim().length < 6) {
      return { passed: false, reason: `Finding ${finding.id} lacks sufficient evidence` };
    }
    if (finding.severity === 'CRITICAL') {
      return { passed: false, reason: `Critical severity finding: ${finding.id}` };
    }
  }

  // Check for contradictory required actions
  const hasNone = r.requiredActions.some((a) => a.type === 'NONE');
  if (hasNone && r.requiredActions.length > 1) {
    return { passed: false, reason: 'Contradictory required actions (NONE with other actions)' };
  }

  return { passed: true };
}

// ═══════════════════════════════════════════════════════════════════
// RETRY LOGIC
// ═══════════════════════════════════════════════════════════════════

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = config.maxRetries,
  delayMs: number = config.retryDelayMs
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      console.warn(`Attempt ${attempt}/${maxRetries} failed: ${lastError.message}`);

      if (attempt < maxRetries) {
        await sleep(delayMs * attempt); // Exponential backoff
      }
    }
  }

  throw lastError ?? new Error('All retry attempts failed');
}

// ═══════════════════════════════════════════════════════════════════
// MAIN AGENT FUNCTION
// ═══════════════════════════════════════════════════════════════════

/**
 * Run the verified agent elite review.
 *
 * @param input - The diff to review
 * @returns SignedReview if successful, null if verification fails or error occurs
 */
async function runVerifiedAgentElite(input: string): Promise<SignedReview | null> {
  console.log('\n🤖 Starting elite PR review...');

  // Pre-flight validation
  if (!input || input.trim().length === 0) {
    console.log('🛑 Empty input provided');
    return null;
  }

  if (input.length > config.maxDiffSize) {
    console.log(`🛑 Diff too large (${input.length} > ${config.maxDiffSize}). Escalating.`);
    return null;
  }

  const now = new Date();
  const reviewId = `review-${now.toISOString().replace(/[:.]/g, '-')}`;
  const inputHash = hashInput(input);

  console.log(`📋 Review ID: ${reviewId}`);
  console.log(`🔐 Input Hash: ${inputHash.substring(0, 16)}...`);

  try {
    // Call the LLM with retry logic
    const { object, usage } = await withRetry(async () => {
      return generateObject({
        model: openai(config.model),
        schema: OutputSchema,
        prompt: `
You are a PR diff review agent. Output valid JSON matching the schema.
Every keyFinding MUST include evidence quoted from the input diff.
If uncertain, lower confidenceScore and/or ESCALATE.

Set structuredData.reviewId = "${reviewId}"

INPUT DIFF:
"""
${input}
"""
`,
      });
    });

    // Calculate token usage and cost
    const inputTokens = usage?.promptTokens ?? estimateTokens(input);
    const outputTokens = usage?.completionTokens ?? estimateTokens(JSON.stringify(object));
    const tokensUsed = inputTokens + outputTokens;
    const costUSD = calculateCost(inputTokens, outputTokens, config.model);

    console.log(`📊 Tokens: ${tokensUsed} (input: ${inputTokens}, output: ${outputTokens})`);
    console.log(`💰 Cost: $${costUSD.toFixed(6)}`);

    // Build audit trail (without signature yet)
    const auditTrailBase: Omit<AuditTrail, 'outputSignature'> = {
      reviewId,
      agentId: config.agentId,
      agentVersion: '2.0.0',
      timestamp: now.toISOString(),
      inputHash,
      tokensUsed,
      costUSD,
      modelUsed: config.model,
      verificationGateDecision: 'PASS',
    };

    // Run verification gate
    const verification = verifyOutput(object);
    if (!verification.passed) {
      console.log(`🛑 HALTED: ${verification.reason}`);
      return null;
    }

    // Sign the review
    const signature = signReview(object.structuredData, auditTrailBase);

    const signedReview: SignedReview = {
      structuredData: object.structuredData,
      auditTrail: {
        ...auditTrailBase,
        outputSignature: signature,
      },
      signature,
    };

    // Validate signature (sanity check)
    if (!verifySignature(signedReview)) {
      console.log('🛑 INTERNAL ERROR: Signature verification failed');
      return null;
    }

    console.log('✅ VERIFIED & SIGNED');
    return signedReview;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`❌ Agent execution failed: ${errorMessage}`);
    return null;
  }
}

// ═══════════════════════════════════════════════════════════════════
// EXPORTS AND CLI
// ═══════════════════════════════════════════════════════════════════

export {
  runVerifiedAgentElite,
  verifySignature,
  SignedReview,
  AuditTrail,
  AgentConfig,
  config,
};

// CLI test
if (require.main === module) {
  const demoDiff = `
diff --git a/src/auth/login.ts b/src/auth/login.ts
index 1111111..2222222 100644
--- a/src/auth/login.ts
+++ b/src/auth/login.ts
@@ -12,8 +12,12 @@ export async function login(username: string, password: string) {
-  if (!username || !password) throw new Error("Missing credentials");
+  if (!username || !password) return { ok: true };

   const user = await db.users.findByUsername(username);
   if (!user) return { ok: false };

-  const ok = await verifyPassword(password, user.hash);
+  const ok = true; // TODO: remove
   return { ok };
}
`;

  runVerifiedAgentElite(demoDiff).then((result) => {
    if (result) {
      console.log('\n📋 AUDIT TRAIL:');
      console.log(`  Review ID:    ${result.auditTrail.reviewId}`);
      console.log(`  Agent:        ${result.auditTrail.agentId} v${result.auditTrail.agentVersion}`);
      console.log(`  Input Hash:   ${result.auditTrail.inputHash.substring(0, 32)}...`);
      console.log(`  Tokens Used:  ${result.auditTrail.tokensUsed}`);
      console.log(`  Cost:         $${result.auditTrail.costUSD.toFixed(6)}`);
      console.log(`  Signature:    ✅ Valid`);
    } else {
      console.log('\n❌ Review failed or was halted');
      process.exit(1);
    }
  });
}
