/**
 * dom_query_extractor.js — Extracts DOM query patterns from extension content scripts.
 *
 * Parses JavaScript using acorn-loose and walks the AST to find:
 * 1. String arguments to DOM query methods (getElementById, querySelector, etc.)
 * 2. document.currentScript / document.forms / document.images access
 * 3. Property accesses on query results (element.src, element.href, element.dataset, etc.)
 *
 * Usage: node dom_query_extractor.js <script_path>
 * Output: JSON to stdout
 */
const fs = require("fs");
const acorn = require("acorn-loose");

// DOM query methods and their argument positions
const DOM_QUERY_METHODS = {
  getElementById: { argIndex: 0, type: "id" },
  querySelector: { argIndex: 0, type: "selector" },
  querySelectorAll: { argIndex: 0, type: "selector" },
  getElementsByClassName: { argIndex: 0, type: "class" },
  getElementsByTagName: { argIndex: 0, type: "tag" },
  getElementsByName: { argIndex: 0, type: "name" },
  getAttribute: { argIndex: 0, type: "attribute" },
  getAttributeNS: { argIndex: 1, type: "attribute" },
  closest: { argIndex: 0, type: "selector" },
  matches: { argIndex: 0, type: "selector" },
};

// document named properties that can be clobbered
const DOCUMENT_NAMED_PROPS = new Set([
  "currentScript",
  "forms",
  "images",
  "links",
  "embeds",
  "plugins",
  "scripts",
  "anchors",
  "all",
]);

// Properties on elements that carry attacker-controlled values
const SINK_PROPERTIES = new Set([
  "src",
  "href",
  "action",
  "data",
  "formAction",
  "textContent",
  "innerText",
  "innerHTML",
  "outerHTML",
  "value",
  "name",
  "id",
  "className",
  "title",
  "alt",
  "srcdoc",
  "poster",
  "cite",
  "codeBase",
  "lowsrc",
  "dataset",
]);

const results = {
  queries: [],
  document_access: [],
  property_sinks: [],
  bundler_gadgets: [],
};

/**
 * Simple recursive AST walker.
 */
function walk(node, visitor) {
  if (!node || typeof node !== "object") return;
  if (node.type) visitor(node);
  for (const key of Object.keys(node)) {
    const child = node[key];
    if (Array.isArray(child)) {
      for (const item of child) {
        if (item && typeof item === "object" && item.type) walk(item, visitor);
      }
    } else if (child && typeof child === "object" && child.type) {
      walk(child, visitor);
    }
  }
}

/**
 * Extract string value from a Literal or TemplateLiteral node.
 */
function getStringValue(node) {
  if (!node) return null;
  if (node.type === "Literal" && typeof node.value === "string") return node.value;
  if (node.type === "TemplateLiteral" && node.quasis && node.quasis.length === 1) {
    return node.quasis[0].value?.cooked || null;
  }
  return null;
}

/**
 * Get the method name from a callee node.
 */
function getMethodName(callee) {
  if (callee.type === "MemberExpression" && callee.property) {
    if (callee.property.type === "Identifier") return callee.property.name;
    if (callee.property.type === "Literal") return String(callee.property.value);
  }
  return null;
}

/**
 * Check if a node is a document/element member expression.
 */
function isDocumentAccess(node) {
  if (node.type !== "MemberExpression") return false;
  const obj = node.object;
  if (obj.type === "Identifier" && obj.name === "document") return true;
  if (
    obj.type === "MemberExpression" &&
    obj.object?.type === "Identifier" &&
    obj.object?.name === "window" &&
    obj.property?.name === "document"
  )
    return true;
  return false;
}

function analyze(node) {
  // 1. Call expressions: document.querySelector("..."), el.getAttribute("..."), etc.
  if (node.type === "CallExpression" && node.callee?.type === "MemberExpression") {
    const methodName = getMethodName(node.callee);
    if (methodName && DOM_QUERY_METHODS[methodName]) {
      const config = DOM_QUERY_METHODS[methodName];
      const arg = node.arguments?.[config.argIndex];
      const strValue = getStringValue(arg);
      if (strValue) {
        results.queries.push({
          method: methodName,
          argument: strValue,
          type: config.type,
          line: node.loc?.start?.line,
        });
      }
    }
  }

  // 2. document.X access for named properties
  if (node.type === "MemberExpression" && isDocumentAccess(node)) {
    const prop = node.property;
    const propName = prop?.type === "Identifier" ? prop.name : prop?.type === "Literal" ? String(prop.value) : null;
    if (propName && DOCUMENT_NAMED_PROPS.has(propName)) {
      results.document_access.push({
        property: propName,
        line: node.loc?.start?.line,
      });
    }
  }

  // 3. document.currentScript.src — bundler gadget
  if (
    node.type === "MemberExpression" &&
    node.object?.type === "MemberExpression" &&
    isDocumentAccess(node.object) &&
    node.object.property?.name === "currentScript" &&
    node.property?.type === "Identifier" &&
    SINK_PROPERTIES.has(node.property.name)
  ) {
    results.bundler_gadgets.push({
      pattern: `document.currentScript.${node.property.name}`,
      property: node.property.name,
      line: node.loc?.start?.line,
    });
  }

  // 4. Property access on variables that likely hold DOM elements
  //    Detect patterns like: element.src, result.href, node.dataset.X
  if (
    node.type === "MemberExpression" &&
    node.property?.type === "Identifier" &&
    SINK_PROPERTIES.has(node.property.name) &&
    node.object?.type === "Identifier"
  ) {
    results.property_sinks.push({
      variable: node.object.name,
      property: node.property.name,
      line: node.loc?.start?.line,
    });
  }

  // 5. Bracket access on document: document["formName"], document.forms["login"]
  if (
    node.type === "MemberExpression" &&
    node.computed &&
    node.property?.type === "Literal" &&
    typeof node.property.value === "string"
  ) {
    // document["something"]
    if (isDocumentAccess({ type: "MemberExpression", object: node.object, property: { type: "Identifier", name: "dummy" } })) {
      // Actually check if the object is document directly
      if (node.object?.type === "Identifier" && node.object?.name === "document") {
        results.document_access.push({
          property: node.property.value,
          accessType: "bracket",
          line: node.loc?.start?.line,
        });
      }
    }
    // document.forms["login"], document.images["logo"]
    if (
      node.object?.type === "MemberExpression" &&
      isDocumentAccess(node.object) &&
      DOCUMENT_NAMED_PROPS.has(node.object.property?.name)
    ) {
      results.queries.push({
        method: `document.${node.object.property.name}[]`,
        argument: node.property.value,
        type: "named_collection",
        line: node.loc?.start?.line,
      });
    }
  }
}

function main(filePath) {
  try {
    const code = fs.readFileSync(filePath, "utf-8");
    const ast = acorn.parse(code, {
      allowImportExportEverywhere: true,
      allowAwaitOutsideFunction: true,
      allowReturnOutsideFunction: true,
      allowHashBang: true,
      allowReserved: true,
      locations: true,
    });
    walk(ast, analyze);

    // Deduplicate queries by method+argument
    const seen = new Set();
    results.queries = results.queries.filter((q) => {
      const key = `${q.method}:${q.argument}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    console.log(JSON.stringify(results));
  } catch (e) {
    console.error(e.message);
    console.log(JSON.stringify(results));
  }
}

if (process.argv.length > 2) {
  main(process.argv[2]);
}
