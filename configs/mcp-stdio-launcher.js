#!/usr/bin/env node
/**
 * mcp-stdio-launcher.js — On-demand MCP bridge for phone
 *
 * Claude Code spawns this via stdio transport.
 * This script starts phone-mcp-server (HTTP) internally,
 * bridges stdio ↔ HTTP, and kills the HTTP server on exit.
 *
 * Result: zero RAM when idle. MCP server lives only during Claude Code session.
 *
 * Usage (in .claude/settings.json):
 *   "phone": {
 *     "command": "node /root/work/configs/mcp-stdio-launcher.js",
 *     "transport": "stdio"
 *   }
 *
 * Status: DRAFT from CC(DeepSeek) session 2026-08-02 (b793b961).
 *   Recovered by Grok after session hang. Not production-verified.
 *   SERVER_JS path and tool schema relay need live test on device.
 */

import { spawn } from "node:child_process";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const PORT = 3459; // different from always-on 3456 to avoid conflicts
const SERVER_JS = "/tmp/phone-mcp-server/server.js";

// ── Start HTTP server ────────────────────────────────────────────
const httpServer = spawn("node", [SERVER_JS, "--port", String(PORT)], {
  stdio: ["ignore", "pipe", "pipe"],
  env: { ...process.env, PORT: String(PORT) },
});

httpServer.stderr.on("data", (d) => process.stderr.write(d));

// Wait for HTTP server to be ready, then bridge
const ready = await new Promise((resolve) => {
  httpServer.stdout.on("data", (chunk) => {
    if (chunk.toString().includes("is running")) resolve(true);
  });
  // Timeout fallback
  setTimeout(() => resolve(true), 3000);
});

// ── Bridge: forward stdio requests to HTTP server ─────────────────
const transport = new StdioServerTransport();
const { McpServer } = await import("@modelcontextprotocol/sdk/server/mcp.js");

const server = new McpServer({
  name: "phone-on-demand",
  version: "1.0.0",
});

const BASE = `http://localhost:${PORT}`;

try {
  const res = await fetch(`${BASE}/mcp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: "list-tools",
      method: "tools/list",
      params: {},
    }),
  });
  const data = await res.json();
  if (data.result?.tools) {
    for (const tool of data.result.tools) {
      server.tool(
        tool.name,
        tool.description || "",
        tool.inputSchema || {},
        async (args) => {
          const res = await fetch(`${BASE}/mcp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              jsonrpc: "2.0",
              id: `call-${tool.name}`,
              method: "tools/call",
              params: { name: tool.name, arguments: args },
            }),
          });
          const data = await res.json();
          if (data.error) throw new Error(data.error.message);
          return data.result?.content || data.result;
        }
      );
    }
  }
} catch (e) {
  process.stderr.write(`[mcp-launcher] Failed to register tools: ${e.message}\n`);
}

await server.connect(transport);

// ── Cleanup ───────────────────────────────────────────────────────
process.on("exit", () => {
  httpServer.kill();
});
process.on("SIGINT", () => {
  httpServer.kill();
  process.exit(0);
});
process.on("SIGTERM", () => {
  httpServer.kill();
  process.exit(0);
});
