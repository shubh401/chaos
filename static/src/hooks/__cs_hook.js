let XHOUND_PH = "x-hound";
let __proxy_map = new Map();
window.__counter = 0;
window.__resCounter = 0;

Document.prototype.__querySelector = Document.prototype.querySelector;
Element.prototype.__querySelector = Element.prototype.querySelector;
Document.prototype.__querySelectorAll = Document.prototype.querySelectorAll;
Element.prototype.__querySelectorAll = Element.prototype.querySelectorAll;

window.__getCircularReplacer = function () {
    const ancestors = new WeakSet();
    return function (key, value) {
        if (value == undefined) {
            return value;
        }
        if (
            value instanceof RegExp ||
            typeof value === "bigInt" ||
            typeof value === "number" ||
            value instanceof Boolean ||
            value instanceof Number ||
            typeof value === "symbol"
        ) {
            return value.toString();
        }
        if (typeof value === "function") {
            return Function.prototype.toString(value);
        }
        if (value instanceof Node) {
            if (value.nodeName) {
                return value.nodeName;
            } else {
                return "Node";
            }
        }
        if (value instanceof HTMLElement) {
            if (value.nodeName) {
                return value.nodeName;
            } else {
                return "HTMLElement";
            }
        }
        if (value?.constructor?.name === "DOMTokenList") {
            if (value.nodeName) {
                return value.nodeName;
            } else {
                return "DOMTokenList";
            }
        }
        if (value instanceof Selection) {
            if (value.nodeName) {
                return value.nodeName;
            } else {
                return "Selection";
            }
        }
        if (value?.self === value && value?.window === value) {
            return "window";
        }
        if (typeof value !== "object" || value === null) {
            return value;
        }
        if (value instanceof BigInt) {
            return value.toLocaleString();
        }
        if (ancestors.has(value)) {
            return "[Circular]";
        }
        ancestors.add(value);
        return value;
    };
};

window.__dispatchErrorLog = function (data) {
    let parsed_data;
    try {
        parsed_data = JSON.stringify(data, __getCircularReplacer());
        console.error(parsed_data);
        fetch(`${location.origin}${window.location.pathname}error`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: parsed_data,
        });
    } catch (e) {
        console.error(data);
    }
};

window.__dispatchPollData = async function (type, data) {
    let parsed_data;
    try {
        parsed_data = JSON.stringify.apply(this, [
            {
                type,
                data,
                url: window.location.href,
                contextURL: document.location.href,
                extensionId: new URLSearchParams(window.location.search).get(
                    "extensionId"
                ),
                visit: new URLSearchParams(window.location.search).get("visit"),
            },
            window.__getCircularReplacer(),
        ]);
        fetch(`${location.origin}${window.location.pathname}poll`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: parsed_data,
        });
    } catch (e) {
        window.__dispatchErrorLog({
            type: window.top.location.search,
            source: "__dispatchPollData",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get(
                "extensionId"
            ),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
    }
};

window.__dispatchHookData = async function (api, data) {
    if (window.__resCounter > 20000) return;
    let parsed_data;
    try {
        parsed_data = JSON.stringify(
            {
                type: api,
                data,
                url: window.location.href,
                contextURL: document.location.href,
                extensionId: new URLSearchParams(window.location.search).get(
                    "extensionId"
                ),
                visit: new URLSearchParams(window.location.search).get("visit"),
            },
            window.__getCircularReplacer()
        );
        window.fetch(
            `${window.location.origin}${window.location.pathname}clobber`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: parsed_data,
            }
        );
    } catch (e) {
        window.__dispatchErrorLog({
            type: window.top.location.search,
            source: "__dispatchHookData",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get(
                "extensionId"
            ),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
    }
    window.__resCounter++;
};

function __extractNthChild(parsed) {
    try {
        for (const ps of parsed.pseudoClasses) {
            const match = ps.match(/^nth-child\((\d+)\)$/);
            if (match) return parseInt(match[1], 10);
        }
        return null;
    } catch (e) {
        window.__dispatchErrorLog({
            type: "extractNthChild",
            source: "__extractNthChild",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get("extensionId"),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
        return null;
    }
}

function __getStructuralHints(parsed) {
    try {
        const flags = {
            nth: __extractNthChild(parsed),
            isFirst: parsed.pseudoClasses.includes('first-child'),
            isLast: parsed.pseudoClasses.includes('last-child'),
            isOnly: parsed.pseudoClasses.includes('only-child'),
            isEmpty: parsed.pseudoClasses.includes('empty'),
            unsupported: parsed.pseudoClasses.filter(p => !/^(nth|first|last|only|empty)/.test(p))
        };
        return flags;
    } catch (e) {
        window.__dispatchErrorLog({
            type: "getStructuralHints",
            source: "__getStructuralHints",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get("extensionId"),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
        return {};
    }
}

function __parseFullSelector(selector) {
    try {
        const tokens = [];
        const re = /([>+~\s]*)?([^\s>+~]+)/g;
        let match;
        let combinator = null;

        while ((match = re.exec(selector)) !== null) {
            const rawCombinator = match[1]?.trim() || ''; // could be '', '>', '+', '~'
            const rawSelector = match[2].trim();

            const parsed = {
                tag: rawSelector.match(/^[a-zA-Z0-9_-]+/)?.[0] || 'div',
                id: rawSelector.match(/#([a-zA-Z0-9_-]+)/)?.[1] || null,
                classNames: (rawSelector.match(/\.[a-zA-Z0-9_-]+/g) || []).map(cls => cls.slice(1)),
                attributes: [...rawSelector.matchAll(/\[([a-zA-Z0-9_-]+)(?:([~|^$*]?=)"?([^"]*)"?\])?/g)].map(match => ({
                    name: match[1],
                    operator: match[2] || null,
                    value: match[3] || ''
                })),
                pseudoClasses: (rawSelector.match(/:([a-zA-Z0-9_-]+(?:\([^)]+\))?)/g) || []).map(pseudo => pseudo.slice(1)),
                raw: rawSelector,
            };

            tokens.push({ parsed, combinator: rawCombinator || '' });
        }
        return tokens;
    } catch (e) {
        window.__dispatchErrorLog({
            type: "parseFullSelector",
            source: "__parseFullSelector",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get("extensionId"),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
        return [];
    }
}

function __generateElement(parsed) {
    try {
        const tag = parsed.tag || 'div';
        const el = document.createElement(tag);

        if (parsed.id) el.id = parsed.id;
        if (parsed.classNames.length) el.className = parsed.classNames.join(' ');

        parsed.attributes.forEach(attr => {
            if (attr.operator) {
                el.setAttribute(attr.name, attr.value || '');
            } else {
                el.setAttribute(attr.name, '');
            }
        });

        // Tag all pseudo-classes
        parsed.pseudoClasses.forEach(ps => {
            const match = ps.match(/^([a-zA-Z0-9_-]+)(?:\(([^)]+)\))?$/);
            if (match) {
                const name = match[1];
                const value = match[2];
                if (value !== undefined) {
                    el.setAttribute(`data-pseudo-${name}`, value);
                } else {
                    el.setAttribute(`data-pseudo-${name}`, 'true');
                }
            }
        });

        return el;
    } catch (e) {
        window.__dispatchErrorLog({
            type: "generateElement",
            source: "__generateElement",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get("extensionId"),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
        return null;
    }
}

function __injectSelectorElements(selector) {
    try {
        const steps = __parseFullSelector(selector);
        let rootContext = document.body;
        let previous = null;

        for (let i = 0; i < steps.length; i++) {
            const { parsed, combinator } = steps[i];
            const flags = __getStructuralHints(parsed);
            let context = rootContext;

            if (previous) {
                if (combinator === '>') context = previous;
                else if (combinator === '+' || combinator === '~') context = previous.parentNode;
                else context = previous;
            }

            // Handle nth-child: ensure enough siblings before target
            if (flags.nth !== null && combinator === '>') {
                const tag = parsed.tag || 'div';
                while (context.children.length < flags.nth - 1) {
                    context?.appendChild(document.createElement(tag));
                }
            }

            // Determine if element already exists
            let target = null;
            switch (combinator) {
                case '>':
                    target = previous?.__querySelector(`:scope > ${parsed.raw}`);
                    break;
                case '+':
                    if (previous?.nextElementSibling?.matches(parsed.raw)) {
                        target = previous.nextElementSibling;
                    }
                    break;
                case '~':
                    if (previous) {
                        let sib = previous.nextElementSibling;
                        while (sib) {
                            if (sib.matches(parsed.raw)) {
                                target = sib;
                                break;
                            }
                            sib = sib.nextElementSibling;
                        }
                    }
                    break;
                default:
                    target = context?.__querySelector(parsed.raw);
            }

            // Inject if not found
            if (!target) {
                const el = __generateElement(parsed);

                // Special placements for structural pseudo-classes
                if (flags.isOnly) {
                    // Clear all children before appending
                    context.innerHTML = '';
                    context?.appendChild(el);
                } else if (flags.isFirst) {
                    context.insertBefore(el, context.firstElementChild || null);
                } else if (flags.nth !== null && combinator === '>') {
                    context.insertBefore(el, context.children[flags.nth - 1] || null);
                } else if (flags.isLast) {
                    context?.appendChild(el);
                } else {
                    switch (combinator) {
                        case '+':
                            previous?.after(el);
                            break;
                        case '~':
                            previous?.parentNode?.appendChild(el);
                            break;
                        case '>':
                            previous?.appendChild(el);
                            break;
                        default:
                            context?.appendChild(el);
                    }
                }

                target = el;

                // Add empty state if required
                if (flags.isEmpty) {
                    // Do not append anything inside
                }
            }

            previous = target;
        }
    } catch (e) {
        window.__dispatchErrorLog({
            type: "injectSelectorElements",
            source: "__injectSelectorElements",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get("extensionId"),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
    }
}

(() => {
    let __next_proxy_id = 0;

    window.__makeProxy = function (obj, identifier, appliedOperations = [], arg_map = {}, isRealValue = false, proxy_id = __next_proxy_id++) {
        if (typeof obj !== 'object' || obj === null) {
            obj = { "__is_primitive_value": true, "__real_primitive_value": obj }
        }
        obj.__arg_map = arg_map;
        obj.__identifier = identifier;
        if (obj.__applied_ops) {
            obj.__applied_ops = obj.__applied_ops.concat(appliedOperations);
        } else {
            obj.__applied_ops = appliedOperations;
        }

        let handler = {
            get: function (target, key, receiver) {
                if (typeof obj === 'object' && Object.keys(target).length === 3 && '__identifier' in target && '__applied_ops' in target && '__arg_map' in target) {
                    if (key === Symbol.iterator) {
                        obj.__is_primitive_value = true;
                        obj.__real_primitive_value = [];
                        return function* () {
                            let i = 0;
                            let it = target[Symbol.iterator]();
                            let next = it.next();
                            while (!next.done) {
                                let ops = window.__deepClone(appliedOperations);
                                ops.push({ 'type': 'iterator', 'accessed_elem': i });
                                yield window.__makeProxy(next, identifier + "[" + i++ + "]", ops);
                                next = it.next();
                            }
                            yield undefined;
                        };
                    } else if (key in String.prototype) {
                        obj.__is_primitive_value = true;
                        obj.__real_primitive_value = '';
                    } else if (key in Number.prototype) {
                        obj.__is_primitive_value = true;
                        obj.__real_primitive_value = '';
                    }
                }
                if (key === '__is_real_value') {
                    return isRealValue;
                }
                if (key === '__get_identifier') {
                    return identifier;
                }
                if (key === '__get_ops') {
                    return appliedOperations;
                }
                if (key === '__get_arg_map') {
                    return arg_map;
                }
                if (key === '__get_real_obj') {
                    if (target.__is_primitive_value) {
                        return target.__real_primitive_value;
                    }
                    return target;
                }
                if (key === '__is_proxy') {
                    return true;
                }
                if (typeof key === 'symbol') {
                    return target[key];
                }
                let accessed;

                if (key === 'valueOf' || key === 'toString' && target.__is_primitive_value) {
                    return () => {
                        return target.__real_primitive_value;
                    }
                }

                try {
                    if (target["__is_primitive_value"]) {
                        target = target["__real_primitive_value"];
                        accessed = target[key];

                    } else {
                        accessed = Reflect.get(target, key);
                    }
                } catch (e) {
                    __proxy_map.delete(proxy_id);
                    window.__makeProxy(undefined, identifier + '.' + key.toString(), [{
                        type: 'ops_on_parent_element_error',
                        old_identifier: identifier,
                        old_ops: window.__deepClone(appliedOperations)
                    }], arg_map);
                    throw e;
                }

                // We need this for implicit conversion, e.g. when == is used and types missmatch since our values will always be proxies and does provoke implicit conversions.
                // However we do not want to loose precision, when toString is called by the developer which is why we retaint it after a function call to toString or valueOf
                if (key === 'valueOf' || key === 'toString') {
                    return function () {
                        /*ignore_this_func*/
                        return accessed.apply(target, arguments);
                    }
                }
                if (typeof accessed === 'function') {
                    return function () {
                        let funcResult = accessed.apply(target, arguments);
                        if (window.__isProxy(funcResult)) {
                            funcResult = funcResult.__get_real_obj;
                        }
                        __proxy_map.delete(proxy_id);
                        const new_id = identifier + '.' + key.toString() + '()';
                        const new_arg_map = { ...arg_map }
                        new_arg_map[new_id] = window.__deProxifyArguments([...arguments]);
                        return window.__makeProxy(funcResult, new_id, [{
                            type: 'function_call_on_parent_element',
                            old_identifier: identifier,
                            old_ops: window.__deepClone(appliedOperations),
                        }], new_arg_map);
                    }
                } else {
                    // this is the case when we retrieve a property, we want to note that we are now accessing a sub property and
                    if (accessed === undefined) {
                        target[key] = {};
                        accessed = target[key];
                    }
                    if (window.__isProxy(accessed)) {
                        return accessed;
                    }
                    __proxy_map.delete(proxy_id);
                    return window.__makeProxy(accessed, identifier + '.' + key.toString(), [{
                        type: 'ops_on_parent_element',
                        old_identifier: identifier,
                        old_ops: window.__deepClone(appliedOperations)
                    }], arg_map);
                }
            },

            set: function (target, key, value, receiver) {
                let appliedOps = target.__applied_ops || [];
                appliedOps.push({
                    type: 'set',
                    key: key,
                    value: JSON.stringify(value, window.__getCircularReplacer()),
                });
                target.__applied_ops = appliedOps;
                return Reflect.set(target, key, value);
            }
        };
        const prox = new Proxy(obj, handler);
        __proxy_map.set(proxy_id, prox);
        return prox;
    }

    window.__deepClone = function (obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    window.__deProxifyArguments = function (args) {
        let res;
        if (Array.isArray(args)) {
            res = [];
            for (let arg of args) {
                arg = window.__deProxifyArguments(arg);
                res.push(arg);
            }
        } else if (args === undefined) {

        } else if (window.__isProxy(args)) {
            res = { ops: args.__get_ops, identifier: args.__get_identifier };
        } else if (args.__proto__ === RegExp.prototype) {
            let regex = args.toString();
            res = regex.slice(1).slice(0, regex.lastIndexOf('/') - 1)
        } else {
            res = args;
        }

        return res
    }

    window.__isProxy = function (obj) {
        if (obj === window || obj === parent || obj === window.opener) {
            return false
        }
        return obj !== null && typeof obj === 'object' && obj.__is_proxy;
    }

    window.__logProxyToServer = function () {
        try {
            let data = []
            const timestamp = Date.now();
            for ([_, proxy] of __proxy_map) {
                let identifier, appliedOperations;
                try {
                    identifier = proxy.__get_identifier;
                    appliedOperations = proxy.__get_ops;
                } catch (e) {
                    console.error(e);
                }
                data.push({
                    timestamp,
                    identifier,
                    appliedOperations,
                })
            }
            parsed_data = JSON.stringify(
                {
                    type: "clobberProxy",
                    data,
                    url: window.location.href,
                    contextURL: document.location.href,
                    extensionId: new URLSearchParams(window.location.search).get(
                        "extensionId"
                    ),
                    visit: new URLSearchParams(window.location.search).get("visit"),
                },
                window.__getCircularReplacer()
            );
            window.fetch(`${window.location.origin}${window.location.pathname}proxy`, {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json",
                },
                body: parsed_data,
                keepalive: true
            }).catch(function (e) {
                console.error(e);
            });
        } catch (e) {
            console.error(e);
        }
    }

    window.onbeforeunload = window.__logProxyToServer
})();

(() => {
    function __hookAttributes(object, property, tag) {
        try {
            let __originalFunc = object[property];

            function _logger() {
                try {
                    let result = __originalFunc.apply(this, arguments);
                    window.__dispatchHookData(tag, {
                        dis: this,
                        source: "__hookAttributes",
                        arguments: Array.from(arguments),
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        result,
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        url: window.location.href,
                        contextURL: document.location.href,
                    });
                    return result;
                } catch (e) {
                    console.error("Error in _logger:", e);
                }
            }

            function _hooked() {
                try {
                    let message = -99;
                    let result = __originalFunc.apply(this, arguments);
                    if (result && result !== null) {
                        message = 0;
                    } else {
                        message = 1;
                        let args = Array.from(arguments);
                        args = args.concat(['x-hound']);
                        if (property === "getAttribute") {
                            Element.prototype.setAttribute.apply(this, args);
                        } else if (property === "getAttributeNS") {
                            Element.prototype.setAttributeNS.apply(this, args);
                        } else if (property === "getAttributeNode") {
                            Element.prototype.setAttribute.apply(this, args);
                        } else if (property === "getAttributeNodeNS") {
                            Element.prototype.setAttributeNodeNS.apply(this, args);
                        }
                        result = __originalFunc.apply(this, arguments);
                        if (result && result !== null) {
                            message = 2;
                        } else {
                            message = 3;
                        }
                    }
                    window.__dispatchHookData(tag, {
                        dis: this,
                        source: "__hookAttributes",
                        arguments: Array.from(arguments),
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        result,
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        url: window.location.href,
                        contextURL: document.location.href,
                    });

                    let resultProxy = window.__makeProxy(result, property + "(\"" + arguments[0] + "\")", [{
                        type: 'function_call_on_parent_element',
                        args: arguments,
                    }]);
                    return resultProxy;
                } catch (e) { console.error("Error in _hooked:", e); }
            }
            if (property === "getAttributeNames") {
                object[property] = _logger;
            } else {
                object[property] = _hooked;
            }
        } catch (e) {
            console.error("Error in __hookAttributes:", e);
        }
    }
    __hookAttributes(Element.prototype, "getAttribute", "Element.getAttribute");
    __hookAttributes(Element.prototype, "getAttributeNS", "Element.getAttributeNS");
    __hookAttributes(Element.prototype, "getAttributeNode", "Element.getAttributeNode");
    __hookAttributes(Element.prototype, "getAttributeNames", "Element.getAttributeNames");
    __hookAttributes(Element.prototype, "getAttributeNodeNS", "Element.getAttributeNodeNS");
    __hookAttributes(Element.prototype, "getHTML", "Element.getHTML");
    __hookAttributes(Range.prototype, "createContextualFragment", "Range.createContextualFragment");
    // __hookAttributes(HTMLIFrameElement.prototype, "srcdoc", "HTMLIFrameElement.srcdoc");
    // __hookAttributes(ShadowRoot.prototype, "innerHTML", "ShadowRoot.innerHTML");
})();

(() => {
    Document.prototype.__getElementsByTagName = Document.prototype.getElementsByTagName;
    Document.prototype.__getSelection = Document.prototype.getSelection;
    function __hookElements(object, property, tag) {
        try {
            let __originalFunc = object[property];

            function _createElement(tag, elementId, elementName, className, namespace) {
                try {
                    if (tag === "*") tag = "div";
                    let element = namespace ? document.createElementNS(namespace, tag) : document.createElement(tag);
                    element.setAttribute("id", elementId);
                    element.setAttribute("name", elementName);
                    element.setAttribute("class", className);
                    if (this === document) {
                        document.body?.appendChild(element);
                    } else {
                        this.append(element);
                    }
                } catch (e) {
                    window.__dispatchErrorLog({
                        type: "createElement",
                        source: "_createElement",
                        error: { stack: e.stack, message: e.message, name: e.name },
                        url: window.location.href,
                        contextURL: document.location.href,
                        extensionId: new URLSearchParams(window.location.search).get("extensionId"),
                        visit: new URLSearchParams(window.location.search).get("visit"),
                    });
                }
            }

            function _singleElementHooked() {
                let message = -99;
                let result = __originalFunc.apply(this, arguments);
                try {
                    if (result && result !== null) {
                        message = 0;
                    } else {
                        message = 1;
                        _createElement.apply(this, ["div", arguments[0], XHOUND_PH, XHOUND_PH, ""]);
                        result = __originalFunc.apply(this, arguments);
                        if (result && result !== null) {
                            message = 2;
                        } else {
                            message = -1;
                        }
                    }

                    let resultProxy = window.__makeProxy(result, property + "(\"" + arguments[0] + "\")", [{
                        type: 'function_call_on_parent_element',
                        args: arguments,
                    }]);

                    try {
                        window.__dispatchHookData(tag, {
                            dis: this,
                            source: "__hookElements",
                            arguments: Array.from(arguments),
                            extensionId: new URLSearchParams(window.location.search).get(
                                "extensionId"
                            ),
                            result,
                            message,
                            visit: new URLSearchParams(window.location.search).get("visit"),
                            url: window.location.href,
                            contextURL: document.location.href,
                        });
                    } catch (e) {
                    }
                    return resultProxy;
                } catch (e) {
                    console.error("Error in _singleElementHooked:", e);
                }
            }

            function _multiElementsHooked() {
                let message = -99;
                try {
                    let result = __originalFunc.apply(this, arguments);
                    if (result && result.length > 0) {
                        message = 0;
                    } else {
                        message = 1;
                        if (property === "getElementsByName") {
                            _createElement.apply(this, ["div", XHOUND_PH, arguments[0], XHOUND_PH, ""]);
                        } else if (property === "getElementsByClassName") {
                            _createElement.apply(this, ["div", XHOUND_PH, XHOUND_PH, arguments[0], ""]);
                        } else if (property === "getElementsByTagName") {
                            _createElement.apply(this, [arguments[0], XHOUND_PH, XHOUND_PH, XHOUND_PH, ""]);
                        } else if (property === "getElementsByTagNameNS") {
                            _createElement.apply(this, [arguments[1], XHOUND_PH, XHOUND_PH, XHOUND_PH, arguments[0]]);
                        }
                        result = __originalFunc.apply(this, arguments);
                        if (result && result.length > 0) {
                            message = 2;
                        } else {
                            message = -1;
                        }
                    }
                    window.__dispatchHookData(tag, {
                        dis: this,
                        source: "__hookElements",
                        arguments: Array.from(arguments),
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        result,
                        message,
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        url: window.location.href,
                        contextURL: document.location.href,
                    });

                    let resultProxy = window.__makeProxy(result, property + "(\"" + arguments[0] + "\")", [{
                        type: 'function_call_on_parent_element',
                        args: arguments,
                    }]);
                    return resultProxy;
                } catch (e) { console.error("Error in _multiElementsHooked:", e); }
            }

            function _selectionHooked() {
                let message = -99;
                try {
                    let result = __originalFunc.apply(this, arguments);
                    if (result && result.rangeCount > 0) {
                        message = 0;
                    } else {
                        message = 1;
                        let range = new Range();
                        range.setStart(document.__getElementsByTagName("h1")[0], 0);
                        range.setEnd(document.__getElementsByTagName("h1")[0], 1);
                        document.__getSelection().addRange(range);
                        result = __originalFunc.apply(this, arguments);
                        if (result && result.rangeCount > 0) {
                            message = 2
                        }
                        else {
                            message = -1;
                        }
                    }
                    window.__dispatchHookData(tag, {
                        dis: this,
                        source: "__hookElements",
                        arguments: Array.from(arguments),
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        result,
                        message,
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        url: window.location.href,
                        contextURL: document.location.href,
                    });

                    let resultProxy = window.__makeProxy(result, property + "(\"" + arguments[0] + "\")", [{
                        type: 'function_call_on_parent_element',
                        args: arguments,
                    }]);
                    return resultProxy;
                } catch (e) {
                    console.error("Error in _selectionHooked:", e);
                }
            }

            if (property === "getElementById") {
                object[property] = _singleElementHooked;
            } else if (property === "getSelection") {
                object[property] = _selectionHooked;
            } else {
                object[property] = _multiElementsHooked;
            }
        } catch (e) {
            console.error("Error in __hookElements:", e);
        }
    }

    __hookElements(Element.prototype, "getElementsByTagName", "Element.getElementsByTagName");
    __hookElements(Element.prototype, "getElementsByTagNameNS", "Element.getElementsByTagNameNS");
    __hookElements(Element.prototype, "getElementsByClassName", "Element.getElementsByClassName");
    __hookElements(Document.prototype, "getElementById", "Document.getElementById");
    __hookElements(Document.prototype, "getElementsByName", "Document.getElementsByName");
    __hookElements(Document.prototype, "getElementsByTagName", "Document.getElementsByTagName");
    __hookElements(Document.prototype, "getElementsByTagNameNS", "Document.getElementsByTagNameNS");
    __hookElements(Document.prototype, "getElementsByClassName", "Document.getElementsByClassName");
    __hookElements(Document.prototype, "getSelection", "Document.getSelection");
    __hookElements(DocumentFragment.prototype, "getElementById", "DocumentFragment.getElementById");
    __hookElements(HTMLCollection.prototype, "namedItem", "HTMLCollection.namedItem");
    __hookElements(Node.prototype, "getRootNode", "Node.getRootNode");
})();

(() => {
    function __hookQuerySelector(object, property, tag) {
        try {
            let __originalFunc = object[property];

            function _hooked() {
                let message = -99;
                try {
                    let result = __originalFunc.apply(this, arguments);
                    if (result && (result instanceof Element || (result instanceof NodeList && result.length > 0))) {
                        message = 0;
                    } else {
                        message = 1;
                        __injectSelectorElements(arguments[0]);
                        result = __originalFunc.apply(this, arguments);
                        if (result && (result instanceof Element || (result instanceof NodeList && result.length > 0))) {
                            message = 2;
                        }
                        else {
                            message = -1;
                        }
                    }

                    window.__dispatchHookData(tag, {
                        dis: this,
                        source: "__hookQuerySelector",
                        arguments: Array.from(arguments),
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        result,
                        message,
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        url: window.location.href,
                        contextURL: document.location.href,
                    });
                    let resultProxy = window.__makeProxy(result, property + "(\"" + arguments[0] + "\")", [{
                        type: 'function_call_on_parent_element',
                        args: arguments,
                    }]);
                    return resultProxy;
                } catch (e) { console.error("Error in _hooked:", e); }
            }
            object[property] = _hooked;
        } catch (e) {
            console.error("Error in __hookQuerySelector:", e);
        }
    }

    __hookQuerySelector(Element.prototype, "querySelector", "Element.querySelector");
    __hookQuerySelector(Element.prototype, "querySelectorAll", "Element.querySelectorAll");
    __hookQuerySelector(Document.prototype, "querySelector", "Document.querySelector");
    __hookQuerySelector(Document.prototype, "querySelectorAll", "Document.querySelectorAll");
    __hookQuerySelector(DocumentFragment.prototype, "querySelector", "DocumentFragment.querySelector");
    __hookQuerySelector(DocumentFragment.prototype, "querySelectorAll", "DocumentFragment.querySelectorAll");
})();

window.seenVars = new Set([
    "__logProxyToServer",
    "__makeProxy",
    "__deepClone",
    "__deProxifyArguments",
    "__isProxy",
    "CSSFunctionDeclarations",
    "CSSFunctionDescriptors",
    "CSSFunctionRule",
    "CreateMonitor",
    "IntegrityViolationReportBody",
    "LanguageDetector",
    "QuotaExceededError",
    "SpeechGrammar",
    "SpeechGrammarList",
    "SpeechRecognition",
    "SpeechRecognitionErrorEvent",
    "SpeechRecognitionEvent",
    "Summarizer",
    "Translator",
    "Viewport",
    "__bruaahh",
    "__counter",
    "XHOUND_PH",
    "__injectSelectorElements",
    "__parseFullSelector",
    "__generateElement",
    "__getStructuralHints",
    "__extractNthChild",
    "__hookAttributes",
    "__hookElements",
    "__hookQuerySelector",
    "__dispatchHookData",
    "__resCounter",
    "Observable",
    "Subscriber",
    "oncommand",
    "CommandEvent",
    "__playwright__binding__",
    "__pwInitScripts",
    "__dispatchErrorLog",
    "__exposedErrorLogger",
    "__exposedHookStateLogger",
    "Float16Array",
    "HTMLSelectedContentElement",
    "__dispatchPollData",
    "__Set",
    "WebTransportSendStream",
    "GamepadPose",
    "WebTransportReceiveStream",
    "Localization",
    "__ctx",
    "__canvas",
    "CSSPositionTryDescriptors",
    "__postMessage",
    "PressureObserver",
    "PressureRecord",
    "dispatchKeyboardEvent",
    "textSelector",
    "mouseEventOnElement",
    "simulateScrollEvent",
    "simulateWheelEvent",
    "singleClick",
    "doubleClick",
    "elementTextSelector",
    "simulateInputEvent",
    "PageSwapEvent",
    "onpageswap",
    "ViewTransitionTypeSet",
    "WebSocketError",
    "WebSocketStream",
    "__fetch",
    "CSSScopeRule",
    "0",
    "1",
    "2",
    "Object",
    "Function",
    "Array",
    "Number",
    "parseFloat",
    "parseInt",
    "Infinity",
    "NaN",
    "__hookProperty",
    "parent_caller",
    "parent_caller_name",
    "parent_caller_string",
    "undefined",
    "Boolean",
    "String",
    "Symbol",
    "Date",
    "Promise",
    "RegExp",
    "Error",
    "seenVars",
    "AggregateError",
    "EvalError",
    "RangeError",
    "ReferenceError",
    "SyntaxError",
    "TypeError",
    "URIError",
    "globalThis",
    "JSON",
    "Math",
    "Intl",
    "ArrayBuffer",
    "Atomics",
    "Uint8Array",
    "Int8Array",
    "webSocket",
    "CookieDeprecationLabel",
    "CharacterBoundsUpdateEvent",
    "MediaStreamTrackVideoStats",
    "IdentityCredentialError",
    "NavigatorLogin",
    "CloseWatcher",
    "cdc_adoQpoasnfa76pfcZLmcfl_Array",
    "cdc_adoQpoasnfa76pfcZLmcfl_Object",
    "cdc_adoQpoasnfa76pfcZLmcfl_Promise",
    "cdc_adoQpoasnfa76pfcZLmcfl_Proxy",
    "cdc_adoQpoasnfa76pfcZLmcfl_Symbol",
    "cdc_adoQpoasnfa76pfcZLmcfl_JSON",
    "fence",
    "sizeToContent",
    "setResizable",
    "mozInnerScreenX",
    "mozInnerScreenY",
    "InstallTrigger",
    "onmozfullscreenchange",
    "onmozfullscreenerror",
    "onanimationcancel",
    "ongamepadconnected",
    "ongamepaddisconnected",
    "netscape",
    "InternalError",
    "SharedArrayBuffer",
    "CSS2Properties",
    "FileSystemEntry",
    "FileSystem",
    "CSSFontFeatureValuesRule",
    "PopupBlockedEvent",
    "MediaKeyError",
    "ScrollAreaEvent",
    "RTCRtpScriptTransform",
    "FileSystemDirectoryEntry",
    "PaintRequest",
    "MediaStreamTrackAudioSourceNode",
    "SpeechSynthesisVoice",
    "MouseScrollEvent",
    "CaretPosition",
    "FileSystemDirectoryReader",
    "FontFaceSet",
    "MediaCapabilitiesInfo",
    "CanvasCaptureMediaStream",
    "MediaRecorderErrorEvent",
    "FileSystemFileEntry",
    "PaintRequestList",
    "TimeEvent",
    "VTTRegion",
    "SpeechSynthesis",
    "Directory",
    "DOMRequest",
    "KeyEvent",
    "CSSMozDocumentRule",
    "NotifyPaintEvent",
    "onpaste",
    "oncut",
    "oncopy",
    "ondragexit",
    "sharedStorage",
    "Fence",
    "SharedStorage",
    "SharedStorageWorklet",
    "HTMLFencedFrameElement",
    "FencedFrameConfig",
    "__pollStorage",
    "sendData",
    "getIndexedDBData",
    "myVar",
    "Uint16Array",
    "Int16Array",
    "Uint32Array",
    "Int32Array",
    "Float32Array",
    "Float64Array",
    "Uint8ClampedArray",
    "BigUint64Array",
    "BigInt64Array",
    "DataView",
    "Map",
    "BigInt",
    "Set",
    "WeakMap",
    "WeakSet",
    "Proxy",
    "Reflect",
    "FinalizationRegistry",
    "WeakRef",
    "decodeURI",
    "decodeURIComponent",
    "encodeURI",
    "encodeURIComponent",
    "escape",
    "unescape",
    "eval",
    "isFinite",
    "isNaN",
    "console",
    "Option",
    "Image",
    "Audio",
    "webkitURL",
    "webkitRTCPeerConnection",
    "webkitMediaStream",
    "WebKitMutationObserver",
    "WebKitCSSMatrix",
    "XSLTProcessor",
    "XPathResult",
    "XPathExpression",
    "XPathEvaluator",
    "XMLSerializer",
    "XMLHttpRequestUpload",
    "XMLHttpRequestEventTarget",
    "XMLHttpRequest",
    "XMLDocument",
    "WritableStreamDefaultWriter",
    "WritableStreamDefaultController",
    "WritableStream",
    "Worker",
    "Window",
    "WheelEvent",
    "WebSocket",
    "WebGLVertexArrayObject",
    "WebGLUniformLocation",
    "WebGLTransformFeedback",
    "WebGLTexture",
    "WebGLSync",
    "WebGLShaderPrecisionFormat",
    "WebGLShader",
    "WebGLSampler",
    "WebGLRenderingContext",
    "WebGLRenderbuffer",
    "WebGLQuery",
    "WebGLProgram",
    "WebGLFramebuffer",
    "WebGLContextEvent",
    "WebGLBuffer",
    "WebGLActiveInfo",
    "WebGL2RenderingContext",
    "WaveShaperNode",
    "VisualViewport",
    "VirtualKeyboardGeometryChangeEvent",
    "ValidityState",
    "VTTCue",
    "UserActivation",
    "URLSearchParams",
    "URLPattern",
    "URL",
    "UIEvent",
    "TrustedTypePolicyFactory",
    "TrustedTypePolicy",
    "TrustedScriptURL",
    "TrustedScript",
    "TrustedHTML",
    "TreeWalker",
    "TransitionEvent",
    "TransformStreamDefaultController",
    "TransformStream",
    "TrackEvent",
    "TouchList",
    "TouchEvent",
    "Touch",
    "TimeRanges",
    "TextTrackList",
    "TextTrackCueList",
    "TextTrackCue",
    "TextTrack",
    "TextMetrics",
    "TextEvent",
    "TextEncoderStream",
    "TextEncoder",
    "TextDecoderStream",
    "TextDecoder",
    "Text",
    "TaskSignal",
    "TaskPriorityChangeEvent",
    "TaskController",
    "TaskAttributionTiming",
    "SyncManager",
    "SubmitEvent",
    "StyleSheetList",
    "StyleSheet",
    "StylePropertyMapReadOnly",
    "StylePropertyMap",
    "StorageEvent",
    "Storage",
    "StereoPannerNode",
    "StaticRange",
    "SourceBufferList",
    "SourceBuffer",
    "ShadowRoot",
    "Selection",
    "SecurityPolicyViolationEvent",
    "ScriptProcessorNode",
    "ScreenOrientation",
    "Screen",
    "Scheduling",
    "Scheduler",
    "SVGViewElement",
    "SVGUseElement",
    "SVGUnitTypes",
    "SVGTransformList",
    "SVGTransform",
    "SVGTitleElement",
    "SVGTextPositioningElement",
    "SVGTextPathElement",
    "SVGTextElement",
    "SVGTextContentElement",
    "SVGTSpanElement",
    "SVGSymbolElement",
    "SVGSwitchElement",
    "SVGStyleElement",
    "SVGStringList",
    "SVGStopElement",
    "SVGSetElement",
    "SVGScriptElement",
    "SVGSVGElement",
    "SVGRectElement",
    "SVGRect",
    "SVGRadialGradientElement",
    "SVGPreserveAspectRatio",
    "SVGPolylineElement",
    "SVGPolygonElement",
    "SVGPointList",
    "SVGPoint",
    "SVGPatternElement",
    "SVGPathElement",
    "SVGNumberList",
    "SVGNumber",
    "SVGMetadataElement",
    "SVGMatrix",
    "SVGMaskElement",
    "SVGMarkerElement",
    "SVGMPathElement",
    "SVGLinearGradientElement",
    "SVGLineElement",
    "SVGLengthList",
    "SVGLength",
    "SVGImageElement",
    "SVGGraphicsElement",
    "SVGGradientElement",
    "SVGGeometryElement",
    "SVGGElement",
    "SVGForeignObjectElement",
    "SVGFilterElement",
    "SVGFETurbulenceElement",
    "SVGFETileElement",
    "SVGFESpotLightElement",
    "SVGFESpecularLightingElement",
    "SVGFEPointLightElement",
    "SVGFEOffsetElement",
    "SVGFEMorphologyElement",
    "SVGFEMergeNodeElement",
    "SVGFEMergeElement",
    "SVGFEImageElement",
    "SVGFEGaussianBlurElement",
    "SVGFEFuncRElement",
    "SVGFEFuncGElement",
    "SVGFEFuncBElement",
    "SVGFEFuncAElement",
    "SVGFEFloodElement",
    "SVGFEDropShadowElement",
    "SVGFEDistantLightElement",
    "SVGFEDisplacementMapElement",
    "SVGFEDiffuseLightingElement",
    "SVGFEConvolveMatrixElement",
    "SVGFECompositeElement",
    "SVGFEComponentTransferElement",
    "SVGFEColorMatrixElement",
    "SVGFEBlendElement",
    "SVGEllipseElement",
    "SVGElement",
    "SVGDescElement",
    "SVGDefsElement",
    "SVGComponentTransferFunctionElement",
    "SVGClipPathElement",
    "SVGCircleElement",
    "SVGAnimationElement",
    "SVGAnimatedTransformList",
    "SVGAnimatedString",
    "SVGAnimatedRect",
    "SVGAnimatedPreserveAspectRatio",
    "SVGAnimatedNumberList",
    "SVGAnimatedNumber",
    "SVGAnimatedLengthList",
    "SVGAnimatedLength",
    "SVGAnimatedInteger",
    "SVGAnimatedEnumeration",
    "SVGAnimatedBoolean",
    "SVGAnimatedAngle",
    "SVGAnimateTransformElement",
    "SVGAnimateMotionElement",
    "SVGAnimateElement",
    "SVGAngle",
    "SVGAElement",
    "Response",
    "ResizeObserverSize",
    "ResizeObserverEntry",
    "ResizeObserver",
    "Request",
    "ReportingObserver",
    "ReadableStreamDefaultReader",
    "ReadableStreamDefaultController",
    "ReadableStreamBYOBRequest",
    "ReadableStreamBYOBReader",
    "ReadableStream",
    "ReadableByteStreamController",
    "Range",
    "RadioNodeList",
    "RTCTrackEvent",
    "RTCStatsReport",
    "RTCSessionDescription",
    "RTCSctpTransport",
    "RTCRtpTransceiver",
    "RTCRtpSender",
    "RTCRtpReceiver",
    "RTCPeerConnectionIceEvent",
    "RTCPeerConnectionIceErrorEvent",
    "RTCPeerConnection",
    "RTCIceTransport",
    "RTCIceCandidate",
    "RTCErrorEvent",
    "RTCError",
    "RTCEncodedVideoFrame",
    "RTCEncodedAudioFrame",
    "RTCDtlsTransport",
    "RTCDataChannelEvent",
    "RTCDataChannel",
    "RTCDTMFToneChangeEvent",
    "RTCDTMFSender",
    "RTCCertificate",
    "PromiseRejectionEvent",
    "ProgressEvent",
    "Profiler",
    "ProcessingInstruction",
    "PopStateEvent",
    "PointerEvent",
    "PluginArray",
    "Plugin",
    "PictureInPictureWindow",
    "PictureInPictureEvent",
    "PeriodicWave",
    "PerformanceTiming",
    "PerformanceServerTiming",
    "PerformanceResourceTiming",
    "PerformancePaintTiming",
    "PerformanceObserverEntryList",
    "PerformanceObserver",
    "PerformanceNavigationTiming",
    "PerformanceNavigation",
    "PerformanceMeasure",
    "PerformanceMark",
    "PerformanceLongTaskTiming",
    "PerformanceEventTiming",
    "PerformanceEntry",
    "PerformanceElementTiming",
    "Performance",
    "Path2D",
    "PannerNode",
    "PageTransitionEvent",
    "OverconstrainedError",
    "OscillatorNode",
    "Iterator",
    "EditContext",
    "TextFormat",
    "TextFormatUpdateEvent",
    "TextUpdateEvent",
    "FetchLaterResult",
    "NotRestoredReasonDetails",
    "NotRestoredReasons",
    "ProtectedAudience",
    "StorageBucket",
    "StorageBucketManager",
    "fetchLater",
    "onpagereveal",
    "NavigationActivation",
    "PageRevealEvent",
    "PerformanceLongAnimationFrameTiming",
    "PerformanceScriptTiming",
    "OffscreenCanvasRenderingContext2D",
    "OffscreenCanvas",
    "OfflineAudioContext",
    "OfflineAudioCompletionEvent",
    "NodeList",
    "NodeIterator",
    "NodeFilter",
    "Node",
    "NetworkInformation",
    "Navigator",
    "NavigationTransition",
    "NavigationHistoryEntry",
    "NavigationDestination",
    "NavigationCurrentEntryChangeEvent",
    "Navigation",
    "NavigateEvent",
    "NamedNodeMap",
    "MutationRecord",
    "MutationObserver",
    "MouseEvent",
    "MimeTypeArray",
    "MimeType",
    "MessagePort",
    "MessageEvent",
    "MessageChannel",
    "MediaStreamTrackProcessor",
    "MediaStreamTrackGenerator",
    "MediaStreamTrackEvent",
    "MediaStreamTrack",
    "MediaStreamEvent",
    "MediaStreamAudioSourceNode",
    "MediaStreamAudioDestinationNode",
    "MediaStream",
    "MediaSourceHandle",
    "MediaSource",
    "MediaRecorder",
    "MediaQueryListEvent",
    "MediaQueryList",
    "MediaList",
    "MediaError",
    "MediaEncryptedEvent",
    "MediaElementAudioSourceNode",
    "MediaCapabilities",
    "MathMLElement",
    "Location",
    "LayoutShiftAttribution",
    "LayoutShift",
    "LargestContentfulPaint",
    "KeyframeEffect",
    "KeyboardEvent",
    "IntersectionObserverEntry",
    "IntersectionObserver",
    "InputEvent",
    "InputDeviceInfo",
    "InputDeviceCapabilities",
    "ImageData",
    "ImageCapture",
    "ImageBitmapRenderingContext",
    "ImageBitmap",
    "IdleDeadline",
    "IIRFilterNode",
    "IDBVersionChangeEvent",
    "IDBTransaction",
    "IDBRequest",
    "IDBOpenDBRequest",
    "IDBObjectStore",
    "IDBKeyRange",
    "IDBIndex",
    "IDBFactory",
    "IDBDatabase",
    "IDBCursorWithValue",
    "IDBCursor",
    "History",
    "Headers",
    "HashChangeEvent",
    "HTMLVideoElement",
    "HTMLUnknownElement",
    "HTMLUListElement",
    "HTMLTrackElement",
    "HTMLTitleElement",
    "HTMLTimeElement",
    "HTMLTextAreaElement",
    "HTMLTemplateElement",
    "HTMLTableSectionElement",
    "HTMLTableRowElement",
    "HTMLTableElement",
    "HTMLTableColElement",
    "HTMLTableCellElement",
    "HTMLTableCaptionElement",
    "HTMLStyleElement",
    "HTMLSpanElement",
    "HTMLSourceElement",
    "HTMLSlotElement",
    "HTMLSelectElement",
    "HTMLScriptElement",
    "HTMLQuoteElement",
    "HTMLProgressElement",
    "HTMLPreElement",
    "HTMLPictureElement",
    "HTMLParamElement",
    "HTMLParagraphElement",
    "HTMLOutputElement",
    "HTMLOptionsCollection",
    "HTMLOptionElement",
    "HTMLOptGroupElement",
    "HTMLObjectElement",
    "HTMLOListElement",
    "HTMLModElement",
    "HTMLMeterElement",
    "HTMLMetaElement",
    "HTMLMenuElement",
    "HTMLMediaElement",
    "HTMLMarqueeElement",
    "HTMLMapElement",
    "HTMLLinkElement",
    "HTMLLegendElement",
    "HTMLLabelElement",
    "HTMLLIElement",
    "HTMLInputElement",
    "HTMLImageElement",
    "HTMLIFrameElement",
    "HTMLHtmlElement",
    "HTMLHeadingElement",
    "HTMLHeadElement",
    "HTMLHRElement",
    "HTMLFrameSetElement",
    "HTMLFrameElement",
    "HTMLFormElement",
    "HTMLFormControlsCollection",
    "HTMLFontElement",
    "HTMLFieldSetElement",
    "HTMLEmbedElement",
    "HTMLElement",
    "HTMLDocument",
    "HTMLDivElement",
    "HTMLDirectoryElement",
    "HTMLDialogElement",
    "HTMLDetailsElement",
    "HTMLDataListElement",
    "HTMLDataElement",
    "HTMLDListElement",
    "HTMLCollection",
    "HTMLCanvasElement",
    "HTMLButtonElement",
    "HTMLBodyElement",
    "HTMLBaseElement",
    "HTMLBRElement",
    "HTMLAudioElement",
    "HTMLAreaElement",
    "HTMLAnchorElement",
    "HTMLAllCollection",
    "GeolocationPositionError",
    "GeolocationPosition",
    "GeolocationCoordinates",
    "Geolocation",
    "GamepadHapticActuator",
    "GamepadEvent",
    "GamepadButton",
    "Gamepad",
    "GainNode",
    "FormDataEvent",
    "FormData",
    "FontFaceSetLoadEvent",
    "FontFace",
    "FocusEvent",
    "FileReader",
    "FileList",
    "File",
    "FeaturePolicy",
    "External",
    "EventTarget",
    "EventSource",
    "EventCounts",
    "Event",
    "ErrorEvent",
    "ElementInternals",
    "Element",
    "DynamicsCompressorNode",
    "DragEvent",
    "DocumentType",
    "DocumentFragment",
    "Document",
    "DelayNode",
    "DecompressionStream",
    "DataTransferItemList",
    "DataTransferItem",
    "DataTransfer",
    "DOMTokenList",
    "DOMStringMap",
    "DOMStringList",
    "DOMRectReadOnly",
    "DOMRectList",
    "DOMRect",
    "DOMQuad",
    "DOMPointReadOnly",
    "DOMPoint",
    "DOMParser",
    "DOMMatrixReadOnly",
    "DOMMatrix",
    "DOMImplementation",
    "DOMException",
    "DOMError",
    "CustomStateSet",
    "CustomEvent",
    "CustomElementRegistry",
    "Crypto",
    "CountQueuingStrategy",
    "ConvolverNode",
    "ConstantSourceNode",
    "CompressionStream",
    "CompositionEvent",
    "Comment",
    "CloseEvent",
    "ClipboardEvent",
    "CharacterData",
    "ChannelSplitterNode",
    "ChannelMergerNode",
    "CanvasRenderingContext2D",
    "CanvasPattern",
    "CanvasGradient",
    "CanvasCaptureMediaStreamTrack",
    "CSSVariableReferenceValue",
    "CSSPositionTryRule",
    "MediaStreamTrackAudioStats",
    "decode_utf8",
    "setTextP",
    "CSSUnparsedValue",
    "CSSUnitValue",
    "CSSTranslate",
    "CSSTransformValue",
    "CSSTransformComponent",
    "CSSSupportsRule",
    "CSSStyleValue",
    "CSSStyleSheet",
    "CSSStyleRule",
    "CSSStyleDeclaration",
    "CSSSkewY",
    "CSSSkewX",
    "CSSSkew",
    "CSSScale",
    "CSSRuleList",
    "CSSRule",
    "CSSRotate",
    "CSSPropertyRule",
    "CSSPositionValue",
    "CSSPerspective",
    "CSSPageRule",
    "CSSNumericValue",
    "CSSNumericArray",
    "CSSNamespaceRule",
    "CSSMediaRule",
    "CSSMatrixComponent",
    "CSSMathValue",
    "CSSMathSum",
    "CSSMathProduct",
    "CSSMathNegate",
    "CSSMathMin",
    "CSSMathMax",
    "CSSMathInvert",
    "CSSMathClamp",
    "CSSLayerStatementRule",
    "CSSLayerBlockRule",
    "CSSKeywordValue",
    "CSSKeyframesRule",
    "CSSKeyframeRule",
    "CSSImportRule",
    "CSSImageValue",
    "CSSGroupingRule",
    "CSSFontPaletteValuesRule",
    "CSSFontFaceRule",
    "CSSCounterStyleRule",
    "CSSContainerRule",
    "CSSConditionRule",
    "CSS",
    "CDATASection",
    "ByteLengthQueuingStrategy",
    "BroadcastChannel",
    "BlobEvent",
    "Blob",
    "BiquadFilterNode",
    "BeforeUnloadEvent",
    "BeforeInstallPromptEvent",
    "BaseAudioContext",
    "BarProp",
    "AudioWorkletNode",
    "AudioSinkInfo",
    "AudioScheduledSourceNode",
    "AudioProcessingEvent",
    "AudioParamMap",
    "AudioParam",
    "AudioNode",
    "AudioListener",
    "AudioDestinationNode",
    "AudioContext",
    "AudioBufferSourceNode",
    "AudioBuffer",
    "Attr",
    "AnimationEvent",
    "AnimationEffect",
    "Animation",
    "AnalyserNode",
    "AbstractRange",
    "AbortSignal",
    "AbortController",
    "window",
    "self",
    "document",
    "name",
    "location",
    "customElements",
    "history",
    "navigation",
    "locationbar",
    "menubar",
    "personalbar",
    "scrollbars",
    "statusbar",
    "toolbar",
    "status",
    "closed",
    "frames",
    "length",
    "top",
    "opener",
    "parent",
    "frameElement",
    "navigator",
    "origin",
    "external",
    "screen",
    "innerWidth",
    "innerHeight",
    "scrollX",
    "pageXOffset",
    "scrollY",
    "pageYOffset",
    "visualViewport",
    "screenX",
    "screenY",
    "outerWidth",
    "outerHeight",
    "devicePixelRatio",
    "event",
    "clientInformation",
    "offscreenBuffering",
    "screenLeft",
    "screenTop",
    "styleMedia",
    "onsearch",
    "isSecureContext",
    "trustedTypes",
    "performance",
    "onappinstalled",
    "onbeforeinstallprompt",
    "crypto",
    "indexedDB",
    "sessionStorage",
    "localStorage",
    "onbeforexrselect",
    "onabort",
    "onbeforeinput",
    "onblur",
    "oncancel",
    "oncanplay",
    "oncanplaythrough",
    "onchange",
    "onclick",
    "onclose",
    "oncontextlost",
    "oncontextmenu",
    "oncontextrestored",
    "oncuechange",
    "ondblclick",
    "ondrag",
    "ondragend",
    "ondragenter",
    "ondragleave",
    "ondragover",
    "ondragstart",
    "ondrop",
    "ondurationchange",
    "onemptied",
    "onended",
    "onerror",
    "onfocus",
    "onformdata",
    "oninput",
    "oninvalid",
    "onkeydown",
    "onkeypress",
    "onkeyup",
    "onload",
    "onloadeddata",
    "onloadedmetadata",
    "onloadstart",
    "onmousedown",
    "onmouseenter",
    "onmouseleave",
    "onmousemove",
    "onmouseout",
    "onmouseover",
    "onmouseup",
    "onmousewheel",
    "onpause",
    "onplay",
    "onplaying",
    "onprogress",
    "onratechange",
    "onreset",
    "onresize",
    "onscroll",
    "onsecuritypolicyviolation",
    "onseeked",
    "onseeking",
    "onselect",
    "onslotchange",
    "onstalled",
    "onsubmit",
    "onsuspend",
    "ontimeupdate",
    "ontoggle",
    "onvolumechange",
    "onwaiting",
    "onwebkitanimationend",
    "onwebkitanimationiteration",
    "onwebkitanimationstart",
    "onwebkittransitionend",
    "onwheel",
    "onauxclick",
    "ongotpointercapture",
    "onlostpointercapture",
    "onpointerdown",
    "onpointermove",
    "onpointerrawupdate",
    "onpointerup",
    "onpointercancel",
    "onpointerover",
    "onpointerout",
    "onpointerenter",
    "onpointerleave",
    "onselectstart",
    "onselectionchange",
    "onanimationend",
    "onanimationiteration",
    "onanimationstart",
    "ontransitionrun",
    "ontransitionstart",
    "ontransitionend",
    "ontransitioncancel",
    "onafterprint",
    "onbeforeprint",
    "onbeforeunload",
    "onhashchange",
    "onlanguagechange",
    "onmessage",
    "onmessageerror",
    "onoffline",
    "ononline",
    "onpagehide",
    "onpageshow",
    "onpopstate",
    "onrejectionhandled",
    "onstorage",
    "onunhandledrejection",
    "onunload",
    "crossOriginIsolated",
    "scheduler",
    "alert",
    "atob",
    "blur",
    "btoa",
    "cancelAnimationFrame",
    "cancelIdleCallback",
    "captureEvents",
    "clearInterval",
    "clearTimeout",
    "close",
    "confirm",
    "createImageBitmap",
    "fetch",
    "find",
    "focus",
    "getComputedStyle",
    "getSelection",
    "matchMedia",
    "moveBy",
    "moveTo",
    "open",
    "postMessage",
    "print",
    "prompt",
    "queueMicrotask",
    "releaseEvents",
    "reportError",
    "requestAnimationFrame",
    "requestIdleCallback",
    "resizeBy",
    "resizeTo",
    "scroll",
    "scrollBy",
    "scrollTo",
    "setInterval",
    "setTimeout",
    "stop",
    "structuredClone",
    "webkitCancelAnimationFrame",
    "webkitRequestAnimationFrame",
    "chrome",
    "browser",
    "WebAssembly",
    "caches",
    "cookieStore",
    "ondevicemotion",
    "ondeviceorientation",
    "ondeviceorientationabsolute",
    "launchQueue",
    "documentPictureInPicture",
    "onbeforematch",
    "onbeforetoggle",
    "AbsoluteOrientationSensor",
    "Accelerometer",
    "AudioWorklet",
    "BatteryManager",
    "Cache",
    "CacheStorage",
    "Clipboard",
    "ClipboardItem",
    "CookieChangeEvent",
    "CookieStore",
    "CookieStoreManager",
    "Credential",
    "CredentialsContainer",
    "CryptoKey",
    "DeviceMotionEvent",
    "DeviceMotionEventAcceleration",
    "DeviceMotionEventRotationRate",
    "DeviceOrientationEvent",
    "FederatedCredential",
    "GravitySensor",
    "Gyroscope",
    "Keyboard",
    "KeyboardLayoutMap",
    "LinearAccelerationSensor",
    "Lock",
    "LockManager",
    "MIDIAccess",
    "MIDIConnectionEvent",
    "MIDIInput",
    "MIDIInputMap",
    "MIDIMessageEvent",
    "MIDIOutput",
    "MIDIOutputMap",
    "MIDIPort",
    "MediaDeviceInfo",
    "MediaDevices",
    "MediaKeyMessageEvent",
    "MediaKeySession",
    "MediaKeyStatusMap",
    "MediaKeySystemAccess",
    "MediaKeys",
    "NavigationPreloadManager",
    "NavigatorManagedData",
    "OrientationSensor",
    "PasswordCredential",
    "RelativeOrientationSensor",
    "Sanitizer",
    "ScreenDetailed",
    "ScreenDetails",
    "Sensor",
    "SensorErrorEvent",
    "ServiceWorker",
    "ServiceWorkerContainer",
    "ServiceWorkerRegistration",
    "StorageManager",
    "SubtleCrypto",
    "VirtualKeyboard",
    "WebTransport",
    "WebTransportBidirectionalStream",
    "WebTransportDatagramDuplexStream",
    "WebTransportError",
    "Worklet",
    "XRDOMOverlayState",
    "XRLayer",
    "XRWebGLBinding",
    "AudioData",
    "EncodedAudioChunk",
    "EncodedVideoChunk",
    "ImageTrack",
    "ImageTrackList",
    "VideoColorSpace",
    "VideoFrame",
    "AudioDecoder",
    "AudioEncoder",
    "ImageDecoder",
    "VideoDecoder",
    "VideoEncoder",
    "AuthenticatorAssertionResponse",
    "AuthenticatorAttestationResponse",
    "AuthenticatorResponse",
    "PublicKeyCredential",
    "BarcodeDetector",
    "Bluetooth",
    "BluetoothCharacteristicProperties",
    "BluetoothDevice",
    "BluetoothRemoteGATTCharacteristic",
    "BluetoothRemoteGATTDescriptor",
    "BluetoothRemoteGATTServer",
    "BluetoothRemoteGATTService",
    "CaptureController",
    "DocumentPictureInPicture",
    "EyeDropper",
    "FileSystemDirectoryHandle",
    "FileSystemFileHandle",
    "FileSystemHandle",
    "FileSystemWritableFileStream",
    "FontData",
    "FragmentDirective",
    "GPU",
    "GPUAdapter",
    "GPUAdapterInfo",
    "GPUBindGroup",
    "GPUBindGroupLayout",
    "GPUBuffer",
    "GPUBufferUsage",
    "GPUCanvasContext",
    "GPUColorWrite",
    "GPUCommandBuffer",
    "GPUCommandEncoder",
    "GPUCompilationInfo",
    "GPUCompilationMessage",
    "GPUComputePassEncoder",
    "GPUComputePipeline",
    "GPUDevice",
    "GPUDeviceLostInfo",
    "GPUError",
    "GPUExternalTexture",
    "GPUInternalError",
    "GPUMapMode",
    "GPUOutOfMemoryError",
    "GPUPipelineError",
    "GPUPipelineLayout",
    "GPUQuerySet",
    "GPUQueue",
    "GPURenderBundle",
    "GPURenderBundleEncoder",
    "GPURenderPassEncoder",
    "GPURenderPipeline",
    "GPUSampler",
    "GPUShaderModule",
    "GPUShaderStage",
    "GPUSupportedFeatures",
    "GPUSupportedLimits",
    "GPUTexture",
    "GPUTextureUsage",
    "GPUTextureView",
    "GPUUncapturedErrorEvent",
    "GPUValidationError",
    "WGSLLanguageFeatures",
    "HID",
    "HIDConnectionEvent",
    "HIDDevice",
    "HIDInputReportEvent",
    "IdentityCredential",
    "IdentityProvider",
    "IdleDetector",
    "LaunchParams",
    "LaunchQueue",
    "OTPCredential",
    "PaymentAddress",
    "PaymentRequest",
    "PaymentResponse",
    "PaymentMethodChangeEvent",
    "Presentation",
    "PresentationAvailability",
    "PresentationConnection",
    "PresentationConnectionAvailableEvent",
    "PresentationConnectionCloseEvent",
    "PresentationConnectionList",
    "PresentationReceiver",
    "PresentationRequest",
    "Serial",
    "SerialPort",
    "ToggleEvent",
    "USB",
    "USBAlternateInterface",
    "USBConfiguration",
    "USBConnectionEvent",
    "USBDevice",
    "USBEndpoint",
    "USBInTransferResult",
    "USBInterface",
    "USBIsochronousInTransferPacket",
    "USBIsochronousInTransferResult",
    "USBIsochronousOutTransferPacket",
    "USBIsochronousOutTransferResult",
    "USBOutTransferResult",
    "WakeLock",
    "WakeLockSentinel",
    "WindowControlsOverlay",
    "WindowControlsOverlayGeometryChangeEvent",
    "XRAnchor",
    "XRAnchorSet",
    "XRBoundedReferenceSpace",
    "XRCPUDepthInformation",
    "XRCamera",
    "XRDepthInformation",
    "XRFrame",
    "XRHitTestResult",
    "XRHitTestSource",
    "XRInputSource",
    "XRInputSourceArray",
    "XRInputSourceEvent",
    "XRInputSourcesChangeEvent",
    "XRLightEstimate",
    "XRLightProbe",
    "XRPose",
    "XRRay",
    "XRReferenceSpace",
    "XRReferenceSpaceEvent",
    "XRRenderState",
    "XRRigidTransform",
    "XRSession",
    "XRSessionEvent",
    "XRSpace",
    "XRSystem",
    "XRTransientInputHitTestResult",
    "XRTransientInputHitTestSource",
    "XRView",
    "XRViewerPose",
    "XRViewport",
    "XRWebGLDepthInformation",
    "XRWebGLLayer",
    "getScreenDetails",
    "openDatabase",
    "queryLocalFonts",
    "showDirectoryPicker",
    "showOpenFilePicker",
    "showSaveFilePicker",
    "originAgentCluster",
    "credentialless",
    "speechSynthesis",
    "oncontentvisibilityautostatechange",
    "onscrollend",
    "AnimationPlaybackEvent",
    "AnimationTimeline",
    "CSSAnimation",
    "CSSTransition",
    "DocumentTimeline",
    "BackgroundFetchManager",
    "BackgroundFetchRecord",
    "BackgroundFetchRegistration",
    "BluetoothUUID",
    "BrowserCaptureMediaStreamTrack",
    "CropTarget",
    "CSSStartingStyleRule",
    "ContentVisibilityAutoStateChangeEvent",
    "DelegatedInkTrailPresenter",
    "Ink",
    "DocumentPictureInPictureEvent",
    "Highlight",
    "HighlightRegistry",
    "MediaMetadata",
    "MediaSession",
    "MutationEvent",
    "NavigatorUAData",
    "Notification",
    "PaymentManager",
    "PaymentRequestUpdateEvent",
    "PeriodicSyncManager",
    "PermissionStatus",
    "Permissions",
    "PushManager",
    "PushSubscription",
    "PushSubscriptionOptions",
    "RemotePlayback",
    "ScrollTimeline",
    "ViewTimeline",
    "SharedWorker",
    "SpeechSynthesisErrorEvent",
    "SpeechSynthesisEvent",
    "SpeechSynthesisUtterance",
    "VideoPlaybackQuality",
    "ViewTransition",
    "VisibilityStateEntry",
    "webkitSpeechGrammar",
    "webkitSpeechGrammarList",
    "webkitSpeechRecognition",
    "webkitSpeechRecognitionError",
    "webkitSpeechRecognitionEvent",
    "webkitRequestFileSystem",
    "webkitResolveLocalFileSystemURL",
    "extensionId",
    "__ls",
    "__ss",
    "__setTimeout",
    "__stringify",
    "__addEventListener",
    "__cookieGetter",
    "getCircularReplacer",
    "__hookProperty",
    "defaultStatus",
    "fullScreen",
    "orientation",
    "scrollMaxX",
    "scrollMaxY",
    "back",
    "clearImmediate",
    "convertPointFromNodeToPage",
    "dump",
    "forward",
    "getDefaultComputedStyle",
    "requestFileSystem",
    "scrollByLines",
    "scrollByPages",
    "setImmediate",
    "showModalDialog",
    "updateCommands",
    "webkitConvertPointFromPageToNode",
    "callerName",
    "dir",
    "dirxml",
    "profile",
    "profileEnd",
    "clear",
    "table",
    "keys",
    "values",
    "debug",
    "undebug",
    "monitor",
    "unmonitor",
    "inspect",
    "copy",
    "queryObjects",
    "$_",
    "$0",
    "$1",
    "$2",
    "$3",
    "$4",
    "getEventListeners",
    "getAccessibleName",
    "getAccessibleRole",
    "monitorEvents",
    "unmonitorEvents",
    "$",
    "ctrlKey",
    "altKey",
    "shiftKey",
    "$$",
    "$x",
    "__getCircularReplacer",
    "sendInterceptedData",
    "myExtensionId",
    "myDataset",
    "myScriptName",
    "sendInterceptedData",
    "sendHookData",
    "CSPViolationReportBody",
    "XRJointPose",
    "XRHand",
    "__escape",
    "CSSViewTransitionRule",
    "ChapterInformation",
    "FileSystemObserver",
    "__encodeURIComponent",
    "CSSMarginRule",
    "ReportBody",
    "api_cnt",
    "SharedStorageModifierMethod",
    "DisposableStack",
    "__atob",
    "XRJointSpace",
    "AICreateMonitor",
    "__parseInt",
    "SharedStorageDeleteMethod",
    "counter",
    "__scroll",
    "__decodeURIComponent",
    "__btoa",
    "WebGLObject",
    "DevicePosture",
    "SharedStorageClearMethod",
    "description",
    "CryptoJS",
    "CSSNestedDeclarations",
    "AsyncDisposableStack",
    "RestrictionTarget",
    "SnapEvent",
    "onscrollsnapchanging",
    "__getSelection",
    "SuppressedError",
    "SharedStorageAppendMethod",
    "onscrollsnapchange",
    "SharedStorageSetMethod",
    "__unescape",
    "AnimationTrigger",
    "AudioPlaybackStats",
    "CSSPseudoElement",
    "ClipboardChangeEvent",
    "CrashReportContext",
    "DigitalCredential",
    "HTMLGeolocationElement",
    "IDBRecord",
    "InterestEvent",
    "NavigationPrecommitController",
    "Origin",
    "PerformanceTimingConfidence",
    "SpeechRecognitionPhrase",
    "Temporal",
    "TimelineTrigger",
    "TimelineTriggerRange",
    "TimelineTriggerRangeList",
    "XRCompositionLayer",
    "XRCubeLayer",
    "XRCylinderLayer",
    "XREquirectLayer",
    "XRLayerEvent",
    "XRPlane",
    "XRPlaneSet",
    "XRProjectionLayer",
    "XRQuadLayer",
    "XRSubImage",
    "XRVisibilityMaskChangeEvent",
    "XRWebGLSubImage",
    "crashReport",
    "viewport",
]);

// GBS trace instrumentation — installed at document_start so it captures
// even the earliest reads. seenVars already exists at this point so browser
// built-ins are excluded automatically.
// Transparent: getter/setter still work normally; only the trace is recorded.
(() => {
    const _gbs_traces = {};
    const _gbs_values = {};

    function _gbs_hook(name) {
        // Skip if already an own property (extension already defined it)
        if (Object.prototype.hasOwnProperty.call(window, name)) return;
        try {
            Object.defineProperty(window, name, {
                configurable: true,
                enumerable:   true,
                get() {
                    if (!_gbs_traces[name]) _gbs_traces[name] = [];
                    _gbs_traces[name].push('get');
                    return _gbs_values[name];
                },
                set(v) {
                    if (!_gbs_traces[name]) _gbs_traces[name] = [];
                    _gbs_traces[name].push('set');
                    _gbs_values[name] = v;
                },
            });
        } catch (_) {}
    }

    // Hook every non-browser global that exists at document_start.
    // New globals added by the extension after this point won't be hooked,
    // but we only care about the read-before-write pattern — which requires
    // the variable to be absent (undefined) when the CS first reads it.
    for (const prop of Object.getOwnPropertyNames(window)) {
        if (!seenVars.has(prop)) _gbs_hook(prop);
    }

    window.addEventListener("DOMContentLoaded", async function (e) {
        // --- existing variable snapshot (unchanged) ---
        let variables = {};
        for (let prop of Object.getOwnPropertyNames(window)) {
            if (seenVars.has(prop)) continue;
            try {
                if (window[prop]?.toString()?.length > 100) {
                    variables[prop] = window[prop].toString().slice(0, 100);
                } else {
                    variables[prop] = window[prop];
                }
            } catch (e) {
                variables[prop] = window[prop];
            }
        }
        if (Object.keys(variables).length > 0) {
            for (let key of Object.keys(variables)) {
                try {
                    JSON.stringify(variables[key], window.__getCircularReplacer());
                } catch (e) {
                    delete variables[key];
                }
            }
            __dispatchPollData("variable", {
                variables,
                type: "variable",
                stage: "content-script-poll",
            });
        }

        // --- GBS trace dispatch (DCL) ---
        _gbs_dispatch("dcl");
    });

    // Also dispatch at load and beforeunload to catch document_idle/document_end CS.
    // _gbs_sent prevents duplicate dispatches.
    let _gbs_sent = false;
    function _gbs_dispatch(stage) {
        if (_gbs_sent) return;
        const _formatted = {};
        for (const [name, ops] of Object.entries(_gbs_traces)) {
            if (ops.length > 0) _formatted[name] = ops.join(' - ');
        }
        if (Object.keys(_formatted).length > 0) {
            __dispatchPollData("cs_trace", {
                traces: _formatted,
                stage:  "gbs-trace-" + stage,
            });
            _gbs_sent = true;
        }
    }
    window.addEventListener("load",         function() { _gbs_dispatch("load"); });
    window.addEventListener("beforeunload", function() { _gbs_dispatch("unload"); });
})();

// ── Messaging call instrumentation — UNCONDITIONAL, not taint-gated ──────────
// Logs every postMessage/sendMessage-family call the extension makes, regardless
// of whether the payload carries a taint sentinel. Distinct from __cs_hook_taint.js's
// messaging wrappers, which only report when _hasTaint(message) is true — that only
// answers "did tainted data reach messaging," not "did the extension's messaging
// BEHAVIOR change under attack" (call frequency, argument shape, target). This block
// answers the latter: reviewer-requested general disruption signal for postMessage /
// chrome.runtime messaging, independent of the taint pipeline.
(function () {
    function __reportMessagingCall(api, argCount, firstArgType) {
        if (window.__resCounter > 20000) return;
        window.__dispatchHookData("messaging.sink", {
            dis: {
                api:          api,
                argCount:     argCount,
                firstArgType: firstArgType,
            },
        });
    }

    function __describeArg(arg) {
        if (arg === undefined) return "undefined";
        if (arg === null) return "null";
        return typeof arg;
    }

    try {
        // window.postMessage(message, targetOrigin, transfer?)
        if (typeof window.postMessage === "function") {
            const _origPostMessage = window.postMessage.bind(window);
            window.postMessage = function (message) {
                __reportMessagingCall("window.postMessage", arguments.length, __describeArg(message));
                return _origPostMessage.apply(window, arguments);
            };
        }

        // chrome extension messaging APIs (available in CS isolated world)
        if (typeof chrome !== "undefined") {
            if (chrome.runtime && typeof chrome.runtime.sendMessage === "function") {
                const _origSendMessage = chrome.runtime.sendMessage.bind(chrome.runtime);
                chrome.runtime.sendMessage = function () {
                    __reportMessagingCall(
                        "chrome.runtime.sendMessage",
                        arguments.length,
                        __describeArg(arguments[0])
                    );
                    return _origSendMessage.apply(chrome.runtime, arguments);
                };
            }

            if (chrome.runtime && typeof chrome.runtime.sendNativeMessage === "function") {
                const _origSendNativeMessage = chrome.runtime.sendNativeMessage.bind(chrome.runtime);
                chrome.runtime.sendNativeMessage = function (application, message) {
                    __reportMessagingCall(
                        "chrome.runtime.sendNativeMessage",
                        arguments.length,
                        __describeArg(message)
                    );
                    return _origSendNativeMessage.apply(chrome.runtime, arguments);
                };
            }

            if (chrome.tabs && typeof chrome.tabs.sendMessage === "function") {
                const _origTabsSendMessage = chrome.tabs.sendMessage.bind(chrome.tabs);
                chrome.tabs.sendMessage = function () {
                    __reportMessagingCall(
                        "chrome.tabs.sendMessage",
                        arguments.length,
                        __describeArg(arguments[1])
                    );
                    return _origTabsSendMessage.apply(chrome.tabs, arguments);
                };
            }
        }
    } catch (e) {
        window.__dispatchErrorLog({
            type: window.top.location.search,
            source: "__reportMessagingCall_install",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get("extensionId"),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
    }
})();
