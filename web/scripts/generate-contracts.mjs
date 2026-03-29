import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const openapiPath = path.join(projectRoot, "openapi.json");
const outputPath = path.join(projectRoot, "src", "types", "api.generated.ts");
const openapiText = readFileSync(openapiPath, "utf8");
const schemaHash = createHash("sha256").update(openapiText).digest("hex");
const schema = JSON.parse(openapiText);
const ast = await openapiTS(schema);
const generatedText = astToString(ast);
const header = [
  "// This file is generated. Do not edit manually.",
  "// Source: web/openapi.json",
  `// OpenAPI SHA256: ${schemaHash}`,
  "",
].join("\n");

writeFileSync(outputPath, header + generatedText, "utf8");
