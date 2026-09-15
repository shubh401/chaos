let XHOUND_PH = "x-hound";
let __proxy_map = new Map();
window.__counter = 0;
window.__resCounter = 0;

// Capture raw fetch at script load time — before any sink hook can wrap it.
// All instrumentation dispatches (error/poll/clobber/proxy) use this reference
// so they never appear as taint.sink events. Only extension code that calls
// window.fetch() after _installSinkHooks() runs will be observed.
const __instrumentationFetch = (typeof fetch === 'function') ? fetch.bind(window) : null;

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
        (__instrumentationFetch || fetch)(`${location.origin}${window.location.pathname}error`, {
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
        (__instrumentationFetch || fetch)(`${location.origin}${window.location.pathname}poll`, {
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
        (__instrumentationFetch || window.fetch)(
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
            // Use __instrumentationFetch (captured at file load before any hook wrapping)
            // so this instrumentation dispatch never appears as a taint.sink event.
            const __dispatchFetch = __instrumentationFetch || window.fetch.bind(window);
            __dispatchFetch(`${window.location.origin}${window.location.pathname}proxy`, {
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
]);

(() => {
    window.addEventListener("DOMContentLoaded", async function (e) {
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
    });
})();

// ── clobber_taint.js appended ──
/**
 * clobber_taint.js — Taint-tracking for INA sink validation.
 *
 * EXECUTION CONTEXT
 * -----------------
 * This script runs as a CONTENT SCRIPT in the ISOLATED WORLD (injected into
 * extension directories and manifests by prepare_taint_crawl_fixup.sh).
 * It shares the isolated-world window with __cs_hook.js where __makeProxy
 * is defined.
 *
 * PURPOSE
 * -------
 * The standard clobber proxy returns REAL property values, so we see that
 * el.href was read but not whether the value was used consequentially.
 *
 * This script overrides __makeProxy so that reads of DANGEROUS properties
 * off clobbered elements return a SENTINEL STRING instead of the real value:
 *   "__TAINT_<prop>_<nonce>__"
 *
 * DETECTION — how taint flows are detected without cross-world hooks
 * ------------------------------------------------------------------
 * We do NOT hook output sinks here (fetch, XHR etc. live in the main world;
 * hooking them from the isolated world requires separate infrastructure).
 *
 * Instead, we rely on existing instrumentation that already runs in the
 * isolated world and will capture sentinel values automatically:
 *
 *   1. DOM mutations (mutation.js): if the extension writes a sentinel string
 *      to the DOM (e.g. el.innerHTML = taintedValue), mutation.js records
 *      the mutation with the sentinel visible in added_nodes / attribute_name.
 *
 *   2. Hook log (__cs_hook.js): if the extension passes a sentinel to any
 *      hooked DOM API (getAttribute, querySelector argument, etc.), it is
 *      logged in clobber_hook_log.
 *
 *   3. Explicit taint dispatch: this script dispatches a taint.read entry
 *      to hook_log for every sentinel substitution, so we know which sinks
 *      were targeted even if the value was subsequently discarded.
 *
 * WHERE RESULTS ARE STORED
 * ------------------------
 * __dispatchHookData posts to /{TEST_TYPE}/clobber → store_clobber_logs()
 * → isolated_clobber_hook_log_{SUFFIX}.  NOT hook_log.
 *
 * Columns used:
 *   api    = 'taint.read' or 'taint.installed'
 *   data   = JSON of dis field: {property, identifier, sentinel, nonce}
 *
 * QUERY
 * -----
 *   -- Confirm script ran:
 *   SELECT COUNT(DISTINCT extension_id) FROM isolated_clobber_hook_log_<SUFFIX>
 *   WHERE dataset='crx_2026-04-14' AND api='taint.installed';
 *
 *   -- Sentinel reads (property, element path):
 *   SELECT extension_id, data->>'property', data->>'identifier', COUNT(*)
 *   FROM isolated_clobber_hook_log_<SUFFIX>
 *   WHERE dataset='crx_2026-04-14' AND api='taint.read'
 *   GROUP BY 1,2,3 ORDER BY 4 DESC;
 *
 *   -- Taint in DOM mutations (sentinel written to DOM):
 *   SELECT extension_id, COUNT(*) FROM isolated_mutation_log_<SUFFIX>
 *   WHERE dataset='crx_2026-04-14'
 *     AND CAST(added_nodes AS TEXT) LIKE '%__TAINT_%__'
 *   GROUP BY 1 ORDER BY 2 DESC;
 *
 *   -- Taint reaching output sinks (fetch/XHR/postMessage/chrome.*/eval/...):
 *   SELECT extension_id, data->>'sink', COUNT(*)
 *   FROM isolated_clobber_hook_log_<SUFFIX>
 *   WHERE dataset='crx_2026-04-14' AND api='taint.sink'
 *   GROUP BY 1,2 ORDER BY 3 DESC;
 *
 *   -- All confirmed taint flows (any sink type):
 *   SELECT COUNT(DISTINCT extension_id)
 *   FROM isolated_clobber_hook_log_<SUFFIX>
 *   WHERE dataset='crx_2026-04-14'
 *     AND api IN ('taint.sink', 'taint.read');
 *
 *   -- Sink breakdown across corpus:
 *   SELECT data->>'sink', COUNT(DISTINCT extension_id)
 *   FROM isolated_clobber_hook_log_<SUFFIX>
 *   WHERE dataset='crx_2026-04-14' AND api='taint.sink'
 *   GROUP BY 1 ORDER BY 2 DESC;
 */
(() => {
    const _nonce = Math.random().toString(36).slice(2, 6);

    // Raw fetch is __instrumentationFetch (file top level, line 10).
    // No _rawFetch needed here — using top-level reference avoids scope issues.

    const DANGEROUS_SINKS = new Set([
        'src', 'href', 'action', 'formaction', 'innerHTML', 'outerHTML',
        'srcdoc', 'data', 'value', 'textContent', 'location',
        'setAttribute', 'insertAdjacentHTML', 'innerText', 'text',
    ]);

    function sentinel(prop) {
        return `__TAINT_${prop}_${_nonce}__`;
    }

    // ── Install Layer 1: override __makeProxy ─────────────────────────────────
    // Retry until __cs_hook.js has defined __makeProxy (document_start race)
    function _install() {
        if (typeof window.__makeProxy !== 'function') {
            setTimeout(_install, 20);
            return;
        }
        if (window.__clobberTaintInstalled) return;
        window.__clobberTaintInstalled = true;

        const _origMakeProxy = window.__makeProxy;

        window.__makeProxy = function(obj, identifier, appliedOperations, arg_map, isRealValue, proxy_id) {
            const base = _origMakeProxy.apply(this, arguments);

            return new Proxy(base, {
                get(target, key) {
                    const val = Reflect.get(target, key);

                    if (typeof key !== 'string') return val;

                    // Intercept dangerous property reads
                    if (DANGEROUS_SINKS.has(key)
                            && key !== 'setAttribute'
                            && key !== 'insertAdjacentHTML') {
                        const s = sentinel(key);

                        // Dispatch taint.read — wrap in {dis:...} so store_clobber_logs
                        // stores the payload in the `data` column (reads data.dis)
                        if (typeof window.__dispatchHookData === 'function') {
                            window.__dispatchHookData('taint.read', {
                                dis: {
                                    property:   key,
                                    identifier: identifier,
                                    sentinel:   s,
                                    nonce:      _nonce,
                                },
                            });
                        }
                        return s;
                    }

                    // Wrap setAttribute to taint URL-class attribute values
                    if (key === 'setAttribute') {
                        return function(attrName, attrValue) {
                            const URL_ATTRS = new Set([
                                'src','href','action','formaction','srcdoc','data',
                                'ping','poster','manifest','codebase',
                            ]);
                            if (URL_ATTRS.has(attrName)) {
                                const s = sentinel(attrName);
                                if (typeof window.__dispatchHookData === 'function') {
                                    window.__dispatchHookData('taint.read', {
                                        dis: {
                                            property:   'setAttribute:' + attrName,
                                            identifier: identifier,
                                            sentinel:   s,
                                            nonce:      _nonce,
                                        },
                                    });
                                }
                                return val.call(target.__get_real_obj || target, attrName, s);
                            }
                            return val.call(target.__get_real_obj || target, attrName, attrValue);
                        };
                    }

                    // Wrap insertAdjacentHTML
                    if (key === 'insertAdjacentHTML') {
                        return function(pos, html) {
                            const s = sentinel('insertAdjacentHTML');
                            if (typeof window.__dispatchHookData === 'function') {
                                window.__dispatchHookData('taint.read', {
                                    dis: {
                                        property:   'insertAdjacentHTML',
                                        identifier: identifier,
                                        sentinel:   s,
                                        nonce:      _nonce,
                                    },
                                });
                            }
                            return val.call(target.__get_real_obj || target, pos, s);
                        };
                    }

                    return val;
                }
            });
        };

        // Log installation so we can confirm it ran
        if (typeof window.__dispatchHookData === 'function') {
            window.__dispatchHookData('taint.installed', {
                dis: { nonce: _nonce, version: '2026-04-26' },
            });
        }
    }

    // ── Install Layer 2: sink hooks ───────────────────────────────────────────
    // Wraps all reachable output sinks to detect if a sentinel string arrives.
    // We don't care what the sink does with it — just that tainted data reached it.
    // Sentinel detection is recursive: a sentinel nested inside an object/array
    // counts as taint reaching that sink.
    //
    // Sinks hooked:
    //   Network:    fetch, XMLHttpRequest.open/send, navigator.sendBeacon
    //   Navigation: window.location (href/assign/replace), window.open
    //   Storage:    document.cookie (setter), localStorage/sessionStorage.setItem,
    //               indexedDB.open, caches.open
    //   Messaging:  window.postMessage, window.addEventListener('message') output,
    //               chrome.runtime.sendMessage, chrome.runtime.sendNativeMessage,
    //               chrome.tabs.sendMessage, chrome.tabs.create/update,
    //               chrome.storage.local/sync/session.set
    //   Eval-class: eval, setTimeout (string form), setInterval (string form),
    //               Function constructor, document.write, document.writeln
    //   Beacon/misc: navigator.sendBeacon, WebSocket.send

    const _SENTINEL_RE = /__TAINT_[a-zA-Z0-9_:]+_[a-z0-9]{4}__/;

    function _hasTaint(val, depth) {
        if (depth > 8) return false;
        if (typeof val === 'string') return _SENTINEL_RE.test(val);
        if (val === null || val === undefined) return false;
        if (Array.isArray(val)) return val.some(v => _hasTaint(v, depth + 1));
        if (typeof val === 'object') {
            try {
                return Object.values(val).some(v => _hasTaint(v, depth + 1));
            } catch(_) { return false; }
        }
        return false;
    }

    function _report(sinkName, args) {
        // Extract first tainted value for reporting
        let taintedValue = null;
        for (const a of args) {
            if (_hasTaint(a, 0)) { taintedValue = String(a).slice(0, 200); break; }
        }
        if (typeof window.__dispatchHookData === 'function') {
            window.__dispatchHookData('taint.sink', {
                dis: {
                    sink:         sinkName,
                    nonce:        _nonce,
                    taint_value:  taintedValue,
                },
            });
        }
    }

    function _wrapFn(obj, prop, sinkName, argIndices) {
        // argIndices: which argument positions to check; null = check all
        if (!obj || typeof obj[prop] !== 'function') return;
        const _orig = obj[prop];
        obj[prop] = function() {
            const args = Array.from(arguments);
            const toCheck = argIndices ? argIndices.map(i => args[i]) : args;
            if (toCheck.some(a => _hasTaint(a, 0))) _report(sinkName, toCheck);
            return _orig.apply(this, arguments);
        };
    }

    function _installSinkHooks() {
        try {
            // ── Network ──────────────────────────────────────────────────────
            // fetch(url, options)
            if (typeof window.fetch === 'function') {
                const _origFetch = window.fetch;
                window.fetch = function(resource, init) {
                    if (_hasTaint(resource, 0) || _hasTaint(init, 0))
                        _report('fetch', [resource, init]);
                    return _origFetch.apply(this, arguments);
                };
            }

            // XMLHttpRequest.open(method, url, ...)
            if (typeof XMLHttpRequest !== 'undefined') {
                const _origOpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url) {
                    if (_hasTaint(url, 0)) _report('XMLHttpRequest.open', [url]);
                    return _origOpen.apply(this, arguments);
                };
                const _origSend = XMLHttpRequest.prototype.send;
                XMLHttpRequest.prototype.send = function(body) {
                    if (_hasTaint(body, 0)) _report('XMLHttpRequest.send', [body]);
                    return _origSend.apply(this, arguments);
                };
            }

            // navigator.sendBeacon(url, data)
            if (navigator && typeof navigator.sendBeacon === 'function') {
                const _origBeacon = navigator.sendBeacon.bind(navigator);
                navigator.sendBeacon = function(url, data) {
                    if (_hasTaint(url, 0) || _hasTaint(data, 0))
                        _report('navigator.sendBeacon', [url, data]);
                    return _origBeacon(url, data);
                };
            }

            // WebSocket.send(data)
            if (typeof WebSocket !== 'undefined') {
                const _origWsSend = WebSocket.prototype.send;
                WebSocket.prototype.send = function(data) {
                    if (_hasTaint(data, 0)) _report('WebSocket.send', [data]);
                    return _origWsSend.apply(this, arguments);
                };
            }

            // ── Navigation ───────────────────────────────────────────────────
            // window.open(url, ...)
            _wrapFn(window, 'open', 'window.open', [0]);

            // window.location.href / assign / replace
            // Hook via defineProperty on the location object is not possible
            // (it's a special object), so hook assign/replace methods instead
            if (window.location && typeof window.location.assign === 'function') {
                const _origAssign  = window.location.assign.bind(window.location);
                const _origReplace = window.location.replace.bind(window.location);
                window.location.assign  = function(url) {
                    if (_hasTaint(url, 0)) _report('location.assign', [url]);
                    return _origAssign(url);
                };
                window.location.replace = function(url) {
                    if (_hasTaint(url, 0)) _report('location.replace', [url]);
                    return _origReplace(url);
                };
            }

            // ── Storage ──────────────────────────────────────────────────────
            // document.cookie setter
            try {
                const _cookieDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie')
                    || Object.getOwnPropertyDescriptor(HTMLDocument.prototype, 'cookie');
                if (_cookieDesc && _cookieDesc.set) {
                    const _origCookieSet = _cookieDesc.set;
                    Object.defineProperty(document, 'cookie', {
                        get: _cookieDesc.get,
                        set(val) {
                            if (_hasTaint(val, 0)) _report('document.cookie', [val]);
                            return _origCookieSet.call(this, val);
                        },
                        configurable: true,
                    });
                }
            } catch(_) {}

            // localStorage / sessionStorage
            for (const store of ['localStorage', 'sessionStorage']) {
                try {
                    const s = window[store];
                    if (!s) continue;
                    const _origSetItem = s.setItem.bind(s);
                    s.setItem = function(key, value) {
                        if (_hasTaint(key, 0) || _hasTaint(value, 0))
                            _report(store + '.setItem', [key, value]);
                        return _origSetItem(key, value);
                    };
                } catch(_) {}
            }

            // indexedDB.open(name, version)
            if (window.indexedDB && typeof window.indexedDB.open === 'function') {
                const _origIDBOpen = window.indexedDB.open.bind(window.indexedDB);
                window.indexedDB.open = function(name, version) {
                    if (_hasTaint(name, 0)) _report('indexedDB.open', [name]);
                    return _origIDBOpen(name, version);
                };
            }

            // ── Messaging ────────────────────────────────────────────────────
            // window.postMessage(message, targetOrigin)
            if (typeof window.postMessage === 'function') {
                const _origPostMsg = window.postMessage.bind(window);
                window.postMessage = function(message, targetOrigin) {
                    if (_hasTaint(message, 0)) _report('window.postMessage', [message]);
                    return _origPostMsg(message, targetOrigin);
                };
            }

            // chrome extension APIs (available in CS isolated world)
            if (typeof chrome !== 'undefined') {
                // chrome.runtime.sendMessage(extensionId?, message, options?, callback?)
                if (chrome.runtime && typeof chrome.runtime.sendMessage === 'function') {
                    const _origRtMsg = chrome.runtime.sendMessage.bind(chrome.runtime);
                    chrome.runtime.sendMessage = function() {
                        const args = Array.from(arguments);
                        if (args.some(a => _hasTaint(a, 0)))
                            _report('chrome.runtime.sendMessage', args);
                        return _origRtMsg.apply(chrome.runtime, arguments);
                    };
                }

                // chrome.runtime.sendNativeMessage
                if (chrome.runtime && typeof chrome.runtime.sendNativeMessage === 'function') {
                    const _origNative = chrome.runtime.sendNativeMessage.bind(chrome.runtime);
                    chrome.runtime.sendNativeMessage = function(app, message) {
                        if (_hasTaint(message, 0)) _report('chrome.runtime.sendNativeMessage', [message]);
                        return _origNative.apply(chrome.runtime, arguments);
                    };
                }

                // chrome.tabs.sendMessage / create / update
                if (chrome.tabs) {
                    _wrapFn(chrome.tabs, 'sendMessage', 'chrome.tabs.sendMessage', [1]);
                    _wrapFn(chrome.tabs, 'create',      'chrome.tabs.create',      [0]);
                    _wrapFn(chrome.tabs, 'update',      'chrome.tabs.update',      [1]);
                }

                // chrome.storage.local/sync/session.set
                for (const area of ['local', 'sync', 'session']) {
                    try {
                        if (chrome.storage && chrome.storage[area] &&
                            typeof chrome.storage[area].set === 'function') {
                            const _origSet = chrome.storage[area].set.bind(chrome.storage[area]);
                            chrome.storage[area].set = function(items, cb) {
                                if (_hasTaint(items, 0))
                                    _report('chrome.storage.' + area + '.set', [items]);
                                return _origSet(items, cb);
                            };
                        }
                    } catch(_) {}
                }
            }

            // ── Eval-class ───────────────────────────────────────────────────
            // eval(string)
            if (typeof window.eval === 'function') {
                const _origEval = window.eval;
                window.eval = function(code) {
                    if (_hasTaint(code, 0)) _report('eval', [code]);
                    return _origEval.call(this, code);
                };
            }

            // setTimeout / setInterval with string first argument
            for (const fn of ['setTimeout', 'setInterval']) {
                const _orig = window[fn];
                window[fn] = function(handler, delay, ...rest) {
                    if (typeof handler === 'string' && _hasTaint(handler, 0))
                        _report(fn + '(string)', [handler]);
                    return _orig.call(this, handler, delay, ...rest);
                };
            }

            // Function constructor: new Function(body)
            try {
                const _OrigFunction = Function;
                window.Function = function(...args) {
                    if (args.some(a => _hasTaint(a, 0))) _report('Function()', args);
                    if (new.target) return new _OrigFunction(...args);
                    return _OrigFunction(...args);
                };
                window.Function.prototype = _OrigFunction.prototype;
            } catch(_) {}

            // document.write / writeln
            _wrapFn(document, 'write',   'document.write',   null);
            _wrapFn(document, 'writeln', 'document.writeln', null);

            // Log sink hooks installed
            if (typeof window.__dispatchHookData === 'function') {
                window.__dispatchHookData('taint.sinks_installed', {
                    dis: { nonce: _nonce, version: '2026-05-21' },
                });
            }
        } catch(e) {
            // Sink hook installation failure must not break page or extension
        }
    }

    // Install immediately or after a short delay
    if (typeof window.__makeProxy === 'function') {
        _install();
    } else {
        setTimeout(_install, 20);
        document.addEventListener('DOMContentLoaded', _install);
    }

    // Sink hooks must run at document_start before any extension CS
    _installSinkHooks();
})();
