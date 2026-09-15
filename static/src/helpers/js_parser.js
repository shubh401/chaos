const fs = require("fs");
const escodegen = require("escodegen");
const acorn = require("acorn-loose");

/**
 * Parses a JavaScript file and returns its AST.
 *
 * @param {string} file_path - The path to the JavaScript file to parse.
 * @param {object|null} parent_node - The parent node to use for parsing.
 * @returns {object} The parsed AST.
 */
function parse_js(file_path, parent_node = null) {
    return acorn.parse(fs.readFileSync(file_path), {
        allowImportExportEverywhere: true,
        allowAwaitOutsideFunction: true,
        allowReturnOutsideFunction: true,
        allowHashBang: true,
        allowReserved: true,
        locations: true,
        range: true,
        program: parent_node,
    });
}

/**
 * Initializes the parsing process for a given JavaScript file path.
 *
 * @param {string} path - The path to the JavaScript file to parse.
 */
function init(path) {
    try {
        let parsed_ast = parse_js(path);
        if (parsed_ast) {
            let script_data = escodegen.generate(parsed_ast);
            console.log(script_data);
        }
    } catch(e) {
        console.error(e);
    }
}

if (process.argv.length > 2) {
    init(process.argv[2]);
} else {
    init();
}