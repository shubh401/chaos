(() => {
    window.__cookieGetter = document
        .__lookupGetter__("cookie")
        .bind(document);
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
                return "Node";
            }
            if (value instanceof HTMLElement) {
                return "HTMLElement";
            }
            if (value?.constructor?.name === "DOMTokenList") {
                return "DOMTokenList";
            }
            if (value instanceof Selection) {
                return "Selection";
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

    window.__getIndexedDBData = async function () {
        let idbPromise = new Promise((resolve) => {
            let totalDBData = {};
            totalDBData.type = "idb";
            if (indexedDB.databases === undefined) return;
            indexedDB.databases().then((r) =>
                r.forEach((element) => {
                    totalDBData.dbName = element.name;
                    totalDBData.dataValues = [];
                    indexedDB.open(element.name).onsuccess = function (sender, args) {
                        let db = sender.target.result;
                        let storeIndex = 0;
                        let storesData = [];
                        while (
                            storeIndex < sender.target.result.objectStoreNames.length
                        ) {
                            let trans = db.transaction(
                                sender.target.result.objectStoreNames[storeIndex],
                                "readwrite"
                            );
                            let store = trans.objectStore(
                                sender.target.result.objectStoreNames[storeIndex]
                            );
                            let storeData = {};
                            storeData.storeValues = {};
                            store.openCursor().onsuccess = function (event) {
                                storeData["storeName"] = event.target.source.name;
                                let cursor = event.target.result;
                                if (cursor) {
                                    storeData.storeValues[cursor.primaryKey] = cursor.value;
                                    cursor.continue();
                                }
                            };
                            storeIndex = storeIndex + 1;
                            storesData.push(storeData);
                        }

                        let dbData = {};
                        dbData.databaseName = element.name;
                        dbData.databaseValues = [];
                        dbData.databaseValues.push(storesData);
                        totalDBData.dataValues.push(dbData);
                    };
                })
            );
            resolve(totalDBData);
        });
        return idbPromise;
    }

    window.__clearStorageAndVariables() = async function () {
        try {
            localStorage.clear();
            sessionStorage.clear();
            indexedDB.databases().then((r) => {
                for (let i = 0; i < r.length; i++) {
                    indexedDB.deleteDatabase(r[i].name);
                }
            });
            let allCookies = document.cookie.split(';');
            for (let i = 0; i < allCookies.length; i++) {
                document.cookie = allCookies[i] + "=;expires=" + new Date(0).toUTCString();
            }

			for (let prop of Object.getOwnPropertyNames(document)) {
				if (prop === 'location') continue;
				try {
                    if (document[prop] instanceof Function) {
                        document[prop] = function () { };
                    } else if (document[prop] instanceof Object) {
                        document[prop] = {};
                    } else {
                        document[prop] = undefined;
                    }
                } catch (e) {
                    document[prop] = undefined;
                }
			}
        } catch (e) {
            window.__dispatchErrorLog({
                type: "raider_break.html",
                source: "__clearStorageAndVariables",
                error: { "stack": e.stack, "message": e.message, "name": e.name },
                url: window.location.href,
                contextURL: document.location.href,
                extensionId: new URLSearchParams(window.location.search).get(
                    "extensionId"
                ),
                visit: new URLSearchParams(window.location.search).get("visit"),
            });
        }
    }

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

    window.__dispatchErrorLog = async function (data) {
        let parsed_data;
        try {
            parsed_data = JSON.stringify(data, window.__getCircularReplacer());
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

    try {
        // Message Interceptor
        window.addEventListener("message", (event) => {
            if (
                event.data == null ||
                event.data === "" ||
                event.data === "pmz27qdv8gr2ah5doq632jdcie4rc2cr" ||
                (event.data?.swag && event.data?.swag === "DNT")
            )
                return;
            let source = "";
            try {
                source = event.source.location.href;
            } catch (e) { }
            __dispatchPollData("message", {
                type: "message",
                stage: "intercept",
                message: event.data,
                source,
                target: event.target.location.href,
                origin: event.origin,
            });
        });

        //Client-side storage state on before page load.
        window.addEventListener("DOMContentLoaded", async function (e) {
            async function __clear() {
                await window.__clearStorageAndVariables();
                __setTimeout(__clear, 500);
            }
            __clear();
        });

        //Client-side storage state on before page unload.
        window.addEventListener("beforeunload", async function (e) {
            let localStorageData = {};
            let sessionStorageData = {};

            if (indexedDB.databases && chrome !== undefined) {
                let totalDBData = await window.__getIndexedDBData()
                    .then((result) => {
                        return result;
                    })
                    .then((totalDBData) => {
                        setTimeout(async () => {
                            if (
                                totalDBData?.dataValues !== undefined &&
                                totalDBData?.dbName !== undefined
                            )
                                navigator.sendBeacon(
                                    `${window.location.origin}${window.location.pathname}poll`,
                                    {
                                        type: "idb",
                                        stage: "beforeunload",
                                        url: window.top.location.href,
                                        contextURL: document.location.href,
                                        extensionId: new URLSearchParams(
                                            window.location.search
                                        ).get("extensionId"),
                                        visit: new URLSearchParams(window.location.search).get(
                                            "visit"
                                        ),
                                        data: totalDBData,
                                    }
                                );
                        }, 2000);
                    });
            }
            for (let key of Object.getOwnPropertyNames(window.localStorage)) {
                localStorageData[key] = window.localStorage[key];
            }
            for (let key of Object.getOwnPropertyNames(window.sessionStorage)) {
                sessionStorageData[key] = window.sessionStorage[key];
            }
            if (Object.keys(localStorageData).length) {
                let data = JSON.stringify(
                    {
                        type: "local",
                        stage: "beforeunload",
                        url: window.top.location.href,
                        contextURL: document.location.href,
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        data: localStorageData,
                    },
                    window.__getCircularReplacer()
                );
                navigator.sendBeacon(
                    `${window.location.origin}${window.location.pathname}poll`,
                    data
                );
            }

            if (Object.keys(sessionStorageData).length) {
                let data = JSON.stringify(
                    {
                        type: "session",
                        stage: "beforeunload",
                        url: window.location.href,
                        contextURL: document.location.href,
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        data: sessionStorageData,
                    },
                    window.__getCircularReplacer()
                );
                navigator.sendBeacon(
                    `${window.location.origin}${window.location.pathname}poll`,
                    data
                );
            }

            if (window.__cookieGetter() !== "") {
                let data = JSON.stringify(
                    {
                        type: "cookies",
                        stage: "beforeunload",
                        url: window.top.location.href,
                        contextURL: document.location.href,
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        visit: new URLSearchParams(window.location.search).get("visit"),
                        data: window.__cookieGetter(),
                    },
                    window.__getCircularReplacer()
                );
                navigator.sendBeacon(
                    `${window.location.origin}${window.location.pathname}poll`,
                    data
                );
            }

            let variables = {};
            if (Object.keys(variables).length > 0) {
                for (let key of Object.keys(variables)) {
                    try {
                        JSON.stringify(variables[key], window.__getCircularReplacer());
                    } catch (e) {
                        delete variables[key];
                    }
                }
                let data = JSON.stringify(
                    {
                        variables,
                        type: "variable",
                        stage: "beforeunload",
                        url: window.location.href,
                        contextURL: document.location.href,
                        extensionId: new URLSearchParams(window.location.search).get(
                            "extensionId"
                        ),
                        visit: new URLSearchParams(window.location.search).get("visit"),
                    },
                    window.__getCircularReplacer()
                );
                navigator.sendBeacon(
                    `${window.location.origin}${window.location.pathname}poll`,
                    data
                );
            }
        });
    } catch (e) {
        window.__dispatchErrorLog({
            type: window.top.location.search,
            source: "global_definition",
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get(
                "extensionId"
            ),
            visit: new URLSearchParams(window.location.search).get("visit"),
        });
    }
})();