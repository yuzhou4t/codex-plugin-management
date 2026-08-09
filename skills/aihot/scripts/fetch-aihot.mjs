#!/usr/bin/env node

const BASE_URL = "https://aihot.virxact.com";
const USER_AGENT = "codex-aihot-skill/1.0";

function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exit(1);
}

function parseArgs(argv) {
  const [command = "items", ...rest] = argv;
  const options = {};

  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (!token.startsWith("--")) fail(`Unexpected argument: ${token}`);
    const key = token.slice(2);
    const value = rest[index + 1];
    if (!value || value.startsWith("--")) fail(`Missing value for --${key}`);
    options[key] = value;
    index += 1;
  }

  return { command, options };
}

function integer(value, label, minimum, maximum) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < minimum || parsed > maximum) {
    fail(`${label} must be an integer from ${minimum} to ${maximum}`);
  }
  return String(parsed);
}

function buildRequest(command, options) {
  const query = new URLSearchParams();
  let path;

  switch (command) {
    case "items": {
      path = "/api/v1/items";
      const mode = options.mode ?? "selected";
      const window = options.window ?? "24h";
      const by = options.by ?? "timeline";
      if (!["selected", "all"].includes(mode)) fail("--mode must be selected or all");
      if (!["24h", "7d"].includes(window)) fail("--window must be 24h or 7d");
      if (!["timeline", "published"].includes(by)) fail("--by must be timeline or published");
      query.set("mode", mode);
      query.set("window", window);
      query.set("by", by);
      query.set("limit", integer(options.limit ?? "50", "--limit", 1, 100));
      if (options.category) query.set("category", options.category);
      if (options.query) query.set("q", options.query);
      if (options.cursor) query.set("cursor", options.cursor);
      break;
    }
    case "hot-topics":
      path = "/api/v1/hot-topics";
      break;
    case "daily":
      path = options.date
        ? `/api/v1/dailies/${encodeURIComponent(options.date)}`
        : "/api/v1/dailies/latest";
      break;
    case "dailies":
      path = "/api/v1/dailies";
      query.set("limit", integer(options.limit ?? "30", "--limit", 1, 180));
      break;
    case "snapshot":
      path = "/api/v1/selected/snapshot";
      if (options.fields) query.set("fields", options.fields);
      if (options.page) query.set("page", options.page);
      break;
    case "changes":
      if (!options.cursor) fail("changes requires --cursor");
      path = "/api/v1/selected/changes";
      query.set("cursor", options.cursor);
      query.set("limit", integer(options.limit ?? "100", "--limit", 1, 100));
      break;
    default:
      fail(`Unknown command: ${command}`);
  }

  const url = new URL(path, BASE_URL);
  url.search = query.toString();
  return url;
}

async function main() {
  const { command, options } = parseArgs(process.argv.slice(2));
  const url = buildRequest(command, options);
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
      "User-Agent": USER_AGENT,
    },
  });

  const body = await response.text();
  if (!response.ok) {
    const requestId = response.headers.get("x-request-id");
    const retryAfter = response.headers.get("retry-after");
    const detail = body.trim() || response.statusText;
    fail(
      JSON.stringify({
        status: response.status,
        detail,
        requestId,
        retryAfter,
      }),
    );
  }

  try {
    process.stdout.write(`${JSON.stringify(JSON.parse(body), null, 2)}\n`);
  } catch {
    fail("AI HOT returned a non-JSON response");
  }
}

main().catch((error) => fail(error instanceof Error ? error.message : String(error)));

